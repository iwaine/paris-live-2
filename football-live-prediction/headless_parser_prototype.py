"""
Prototype: Headless Playwright parser for live match stats (45s updates).
Architecture: Persistent page + MutationObserver + rolling snapshot cache.
Targets: Position et timing live sur SoccerStats.com (intervalle 30-45', 75-90').
"""

import asyncio
import time
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("⚠️  Install: pip install playwright; playwright install chromium")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MatchStats:
    """Live match statistics snapshot."""
    timestamp: float  # seconds since epoch
    minute: Optional[int] = None
    score_home: Optional[int] = None
    score_away: Optional[int] = None
    possession_home: Optional[float] = None  # % as decimal (0.58 = 58%)
    possession_away: Optional[float] = None
    shots_home: Optional[int] = None
    shots_away: Optional[int] = None
    sot_home: Optional[int] = None  # shots on target
    sot_away: Optional[int] = None
    corners_home: Optional[int] = None
    corners_away: Optional[int] = None
    yellow_cards_home: Optional[int] = None
    yellow_cards_away: Optional[int] = None
    red_cards_home: Optional[int] = None
    red_cards_away: Optional[int] = None
    last_events: Optional[List[Dict]] = None  # [{'minute': 45, 'type': 'goal', 'team': 'home'}, ...]
    
    @property
    def age_sec(self) -> float:
        """Seconds since this snapshot was captured."""
        return time.time() - self.timestamp
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SnapshotCache:
    """Rolling window cache for delta calculations."""
    
    def __init__(self, match_id: str, max_snapshots: int = 20):
        self.match_id = match_id
        self.max_snapshots = max_snapshots
        self.snapshots: List[MatchStats] = []
    
    def append(self, stats: MatchStats):
        """Add snapshot to cache, keep only most recent N."""
        self.snapshots.append(stats)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)
        logger.debug(f"[{self.match_id}] Snapshot cache: {len(self.snapshots)} entries")
    
    def get_momentum(self, window_sec: float = 300) -> Optional[Dict]:
        """Calculate deltas over last window_sec seconds."""
        if len(self.snapshots) < 2:
            return None
        
        now = time.time()
        recent = [s for s in self.snapshots if now - s.timestamp <= window_sec]
        
        if len(recent) < 2:
            return None
        
        first, last = recent[0], recent[-1]
        
        deltas = {}
        for key in ['shots_home', 'shots_away', 'sot_home', 'sot_away', 'corners_home', 'corners_away']:
            val_first = getattr(first, key, None)
            val_last = getattr(last, key, None)
            if val_first is not None and val_last is not None:
                deltas[f'{key}_delta'] = val_last - val_first
        
        return deltas if deltas else None


class HeadlessMatchParser:
    """
    Persistent headless browser for parsing live match stats.
    Keeps page open, uses MutationObserver for change detection.
    """
    
    # CSS selectors + fallbacks for robustness
    SELECTORS = {
        'minute': [
            '.match-minute',  # Primary
            '[data-stat="minute"]',
            '//span[contains(text(), "\'")]',  # minute format "45'"
        ],
        'score_home': [
            '.score-home',
            '[data-team="home"] .score',
            'span.home-score',
        ],
        'score_away': [
            '.score-away',
            '[data-team="away"] .score',
            'span.away-score',
        ],
        'possession_home': [
            '.possession-home',
            '[data-stat="possession"] .home-value',
            '.possession-stat .home',
        ],
        'possession_away': [
            '.possession-away',
            '[data-stat="possession"] .away-value',
            '.possession-stat .away',
        ],
        'shots_home': [
            '.shots-home',
            '[data-stat="shots"] .home',
            '.shots-stat .home-value',
        ],
        'shots_away': [
            '.shots-away',
            '[data-stat="shots"] .away',
            '.shots-stat .away-value',
        ],
        'sot_home': [
            '.sot-home',
            '[data-stat="sot"] .home',
            '.shots-on-target .home',
        ],
        'sot_away': [
            '.sot-away',
            '[data-stat="sot"] .away',
            '.shots-on-target .away',
        ],
        'corners_home': [
            '.corners-home',
            '[data-stat="corners"] .home',
        ],
        'corners_away': [
            '.corners-away',
            '[data-stat="corners"] .away',
        ],
        'red_cards_home': [
            '.red-cards-home',
            '[data-card="red"] .home',
        ],
        'red_cards_away': [
            '.red-cards-away',
            '[data-card="red"] .away',
        ],
    }
    
    # MutationObserver injection script
    MUTATION_OBSERVER_SCRIPT = """
    (function() {
        if (window._stats_observer_running) return;
        window._stats_observer_running = true;
        
        window.stat_updates = [];
        
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(m => {
                if (m.type === 'characterData' || m.type === 'attributes') {
                    window.stat_updates.push({
                        timestamp: Date.now(),
                        target_class: m.target.className,
                        text: m.target.textContent?.substring(0, 50)
                    });
                }
            });
        });
        
        const container = document.querySelector('.match-stats, .statistics, [data-stats]');
        if (container) {
            observer.observe(container, {
                subtree: true,
                attributes: true,
                characterData: true,
                childList: false
            });
            console.log('[OBSERVER] Stats container found and monitoring started');
        } else {
            console.warn('[OBSERVER] Stats container not found');
        }
    })();
    """
    
    def __init__(self, match_id: str, match_url: str, interval_sec: float = 45):
        self.match_id = match_id
        self.match_url = match_url
        self.interval_sec = interval_sec
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.cache = SnapshotCache(match_id)
        self.last_valid_stats: Optional[MatchStats] = None
        self.health_check_interval = 300  # 5 minutes
    
    async def initialize(self):
        """Launch browser and navigate to match."""
        logger.info(f"[{self.match_id}] Initializing browser...")
        
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.page = await self.browser.new_page()
        
        # User-Agent rotation (avoid bot detection)
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        import random
        await self.page.set_user_agent(random.choice(user_agents))
        
        logger.info(f"[{self.match_id}] Navigating to {self.match_url}...")
        try:
            await self.page.goto(self.match_url, wait_until='domcontentloaded', timeout=30000)
            logger.info(f"[{self.match_id}] ✅ Page loaded")
        except Exception as e:
            logger.error(f"[{self.match_id}] ❌ Navigation failed: {e}")
            raise
        
        # Inject MutationObserver
        await self.page.evaluate(self.MUTATION_OBSERVER_SCRIPT)
        logger.info(f"[{self.match_id}] ✅ MutationObserver injected")
    
    async def _extract_stat(self, stat_name: str) -> Optional[float]:
        """
        Extract single stat with fallback selectors.
        Returns float (e.g., 58.5 for possession %), or None if all fail.
        """
        selectors = self.SELECTORS.get(stat_name, [])
        
        for selector in selectors:
            try:
                text = await self.page.locator(selector).first.text_content(timeout=2000)
                if text:
                    # Clean: remove %, spaces, leading zeros
                    cleaned = text.strip().replace('%', '').strip()
                    value = float(cleaned)
                    logger.debug(f"[{self.match_id}] {stat_name}={value} (selector: {selector})")
                    return value
            except Exception as e:
                logger.debug(f"[{self.match_id}] Selector '{selector}' failed for {stat_name}: {e}")
                continue
        
        # All selectors failed
        logger.warning(f"[{self.match_id}] ❌ All selectors failed for {stat_name}")
        return None
    
    async def _extract_events(self) -> Optional[List[Dict]]:
        """Parse recent events from match page."""
        try:
            # Try to find events list
            events_text = await self.page.locator('.match-events, .events-list, [data-events]').first.text_content(timeout=2000)
            if events_text:
                logger.debug(f"[{self.match_id}] Events found: {events_text[:100]}...")
                # In real impl: parse events list properly
                return [{'minute': 0, 'type': 'unknown', 'team': 'unknown'}]
        except:
            pass
        
        return None
    
    async def capture_snapshot(self) -> Optional[MatchStats]:
        """Capture current live stats as snapshot."""
        logger.info(f"[{self.match_id}] Capturing snapshot...")
        
        try:
            stats = MatchStats(
                timestamp=time.time(),
                minute=int(await self._extract_stat('minute') or 0),
                score_home=int(await self._extract_stat('score_home') or 0),
                score_away=int(await self._extract_stat('score_away') or 0),
                possession_home=(await self._extract_stat('possession_home')) / 100,
                possession_away=(await self._extract_stat('possession_away')) / 100,
                shots_home=int(await self._extract_stat('shots_home') or 0),
                shots_away=int(await self._extract_stat('shots_away') or 0),
                sot_home=int(await self._extract_stat('sot_home') or 0),
                sot_away=int(await self._extract_stat('sot_away') or 0),
                corners_home=int(await self._extract_stat('corners_home') or 0),
                corners_away=int(await self._extract_stat('corners_away') or 0),
                red_cards_home=int(await self._extract_stat('red_cards_home') or 0),
                red_cards_away=int(await self._extract_stat('red_cards_away') or 0),
                last_events=await self._extract_events(),
            )
            
            self.cache.append(stats)
            self.last_valid_stats = stats
            
            logger.info(f"[{self.match_id}] ✅ Snapshot captured: minute={stats.minute}, "
                       f"score={stats.score_home}-{stats.score_away}, "
                       f"poss={stats.possession_home:.1%}-{stats.possession_away:.1%}")
            
            return stats
        
        except Exception as e:
            logger.error(f"[{self.match_id}] ❌ Snapshot capture failed: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Verify browser is responsive."""
        try:
            result = await self.page.evaluate("1+1", timeout=5000)
            if result == 2:
                logger.debug(f"[{self.match_id}] ✅ Health check OK")
                return True
        except Exception as e:
            logger.error(f"[{self.match_id}] ❌ Health check failed: {e}")
        
        return False
    
    async def recover(self):
        """Restart browser and page."""
        logger.warning(f"[{self.match_id}] 🔄 Attempting recovery...")
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
        except:
            pass
        
        # Reinitialize
        await self.initialize()
    
    async def stream_live_stats(self, max_duration_sec: Optional[float] = None):
        """
        Main loop: yield stats snapshots every interval_sec.
        
        Args:
            max_duration_sec: Stop after this many seconds (for testing). None = indefinite.
        
        Yields:
            MatchStats objects
        """
        await self.initialize()
        
        start_time = time.time()
        last_health_check = start_time
        health_check_task = None
        
        try:
            while True:
                # Health check periodically
                now = time.time()
                if now - last_health_check > self.health_check_interval:
                    if not await self.health_check():
                        await self.recover()
                    last_health_check = now
                
                # Check timeout
                if max_duration_sec and (now - start_time) > max_duration_sec:
                    logger.info(f"[{self.match_id}] Timeout reached ({max_duration_sec}s), stopping.")
                    break
                
                # Capture and yield
                stats = await self.capture_snapshot()
                if stats:
                    yield stats
                
                # Sleep for interval (with small jitter to avoid exact repeats)
                import random
                jitter = random.uniform(-2, 5)  # -2 to +5 seconds
                sleep_time = max(1, self.interval_sec + jitter)
                logger.debug(f"[{self.match_id}] Sleeping {sleep_time:.1f}s until next poll...")
                await asyncio.sleep(sleep_time)
        
        except KeyboardInterrupt:
            logger.info(f"[{self.match_id}] Interrupted by user")
        
        except Exception as e:
            logger.error(f"[{self.match_id}] Fatal error: {e}", exc_info=True)
        
        finally:
            if self.browser:
                await self.browser.close()
                logger.info(f"[{self.match_id}] Browser closed")


async def test_prototype():
    """Test parser with a real SoccerStats match (or mock)."""
    
    # Example: Arsenal vs Chelsea match URL (replace with real URL)
    # For testing, we'll use a simpler approach
    match_url = "https://www.soccerstats.com/match.asp?id=1234567"  # Replace with real URL
    
    parser = HeadlessMatchParser(
        match_id="arsenal_vs_chelsea_2025-11-28",
        match_url=match_url,
        interval_sec=45
    )
    
    logger.info("=" * 80)
    logger.info("🎯 HEADLESS PARSER PROTOTYPE TEST")
    logger.info("=" * 80)
    
    try:
        # Stream stats for 5 minutes (300 sec) for testing
        snapshot_count = 0
        async for stats in parser.stream_live_stats(max_duration_sec=300):
            snapshot_count += 1
            
            # Momentum calculation
            momentum = parser.cache.get_momentum(window_sec=180)
            
            logger.info(f"\n--- Snapshot #{snapshot_count} ---")
            logger.info(f"Timestamp: {datetime.fromtimestamp(stats.timestamp).isoformat()}")
            logger.info(f"Age: {stats.age_sec:.1f}s")
            logger.info(f"Match: Minute {stats.minute}")
            logger.info(f"Score: {stats.score_home}-{stats.score_away}")
            logger.info(f"Possession: {stats.possession_home:.1%} vs {stats.possession_away:.1%}")
            logger.info(f"Shots: {stats.shots_home} vs {stats.shots_away} (SOT: {stats.sot_home} vs {stats.sot_away})")
            logger.info(f"Corners: {stats.corners_home} vs {stats.corners_away}")
            logger.info(f"Red cards: {stats.red_cards_home} vs {stats.red_cards_away}")
            
            if momentum:
                logger.info(f"Momentum (last 3 min): {momentum}")
            
            # Example: detect if in target interval (30-45' or 75-90')
            if stats.minute:
                if 30 <= stats.minute < 45 or 75 <= stats.minute < 90:
                    logger.info(f"🎯 IN TARGET INTERVAL! Ready for danger score calculation.")
                else:
                    logger.info(f"⏭️  Outside target interval ({stats.minute}').")
    
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    # Run test
    asyncio.run(test_prototype())
