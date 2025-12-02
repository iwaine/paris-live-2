#!/usr/bin/env python
"""
PHASE 2 ML MODEL TRAINING STARTER KIT

This template shows how to use the Phase 1 data for training the ML model.

Status: Template ready, waiting for historical_matches.csv from Phase 1 scraper
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, confusion_matrix, classification_report
import lightgbm as lgb
import json
from pathlib import Path
from typing import Tuple, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLModelBuilder:
    """Build and train LightGBM model for "au moins 1 but" prediction."""
    
    # Features expected from feature_extractor.py
    FEATURE_COLUMNS = [
        'minute', 'minute_bucket', 'score_home', 'score_away', 'goal_diff',
        'poss_home', 'poss_away', 'shots_home', 'shots_away',
        'sot_home', 'sot_away', 'shot_accuracy', 'sot_ratio',
        'shot_delta_5m', 'sot_delta_5m', 'corner_delta_5m',
        'red_cards', 'yellow_cards', 'elo_home', 'elo_away', 'elo_diff',
        'recent_goal_count_5m', 'saturation_score',
    ]
    
    # Target column
    TARGET = 'label'
    
    def __init__(self, output_dir: str = 'models'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = None
    
    def load_historical_data(self, csv_path: str) -> pd.DataFrame:
        """Load historical matches from Phase 1 scraper output."""
        logger.info(f"📥 Loading historical data from {csv_path}...")
        
        df = pd.read_csv(csv_path)
        
        logger.info(f"✅ Loaded {len(df)} records ({len(df) // 2} matches)")
        
        # Data validation
        logger.info(f"🔍 Data quality check:")
        logger.info(f"   - Label distribution: {df['label'].value_counts().to_dict()}")
        logger.info(f"   - Missing values: {df.isnull().sum().sum()}")
        logger.info(f"   - Columns: {list(df.columns)}")
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for training.
        
        This assumes df is from historical_scraper.py output with columns:
        [match_id, match_date, league, home_team, away_team, home_goals, away_goals,
         interval_start, interval_end, label, goals_count, goal_minutes]
        """
        logger.info("🔧 Preparing features...")
        
        # For now, we'll use synthetic features based on the match data
        # In practice, you'd merge this with live feature data from feature_extractor.py
        
        # Create feature matrix (synthetic - replace with real features later)
        X = pd.DataFrame()
        
        # Temporal features
        X['minute'] = (df['interval_start'] + df['interval_end']) / 2
        X['minute_bucket'] = df['interval_start']
        
        # Score-based features (from final score)
        X['score_home'] = df['home_goals']
        X['score_away'] = df['away_goals']
        X['goal_diff'] = df['home_goals'] - df['away_goals']
        
        # Possession (synthetic - would come from feature_extractor)
        np.random.seed(42)
        X['poss_home'] = np.random.uniform(40, 60, len(df))
        X['poss_away'] = 100 - X['poss_home']
        
        # Shots (synthetic)
        X['shots_home'] = np.random.poisson(5, len(df))
        X['shots_away'] = np.random.poisson(4, len(df))
        X['sot_home'] = (X['shots_home'] * np.random.uniform(0.2, 0.5, len(df))).astype(int)
        X['sot_away'] = (X['shots_away'] * np.random.uniform(0.2, 0.5, len(df))).astype(int)
        
        # Ratios
        X['shot_accuracy'] = (X['sot_home'] / (X['shots_home'] + 1)) * 100
        X['sot_ratio'] = X['sot_home'] / (X['sot_home'] + X['sot_away'] + 1)
        
        # Deltas (synthetic)
        X['shot_delta_5m'] = np.random.randint(-2, 3, len(df))
        X['sot_delta_5m'] = np.random.randint(-1, 2, len(df))
        X['corner_delta_5m'] = np.random.randint(-1, 3, len(df))
        
        # Cards
        X['red_cards'] = np.random.binomial(1, 0.05, len(df))
        X['yellow_cards'] = np.random.poisson(1.5, len(df))
        
        # Elo (synthetic - would come from team database)
        X['elo_home'] = np.random.uniform(1500, 2100, len(df))
        X['elo_away'] = np.random.uniform(1500, 2100, len(df))
        X['elo_diff'] = X['elo_home'] - X['elo_away']
        
        # Activity
        X['recent_goal_count_5m'] = np.random.binomial(3, 0.3, len(df))
        X['saturation_score'] = np.random.uniform(0, 1, len(df))
        
        # Target
        y = df['label']
        
        logger.info(f"✅ Features prepared: {X.shape[1]} features, {X.shape[0]} samples")
        logger.info(f"   - Class balance: {y.mean():.1%} goals")
        
        return X, y
    
    def train_with_kfold(self, X: pd.DataFrame, y: pd.Series, n_splits: int = 5):
        """
        Train LightGBM with Stratified K-fold CV.
        
        Returns:
        - Trained models (list of 5)
        - Cross-validation scores (list of 5 AUC scores)
        """
        logger.info(f"🎯 Training with {n_splits}-fold Stratified CV...")
        
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        models = []
        cv_scores = []
        predictions_cv = np.zeros(len(X))
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
            logger.info(f"\n📊 Fold {fold}/{n_splits}:")
            
            # Split data
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            
            # Train LightGBM
            model = lgb.LGBMClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                num_leaves=31,
                random_state=42,
                verbosity=-1,
                is_unbalanced=True,  # Handle class imbalance
            )
            
            model.fit(
                X_train_scaled, y_train,
                eval_set=[(X_val_scaled, y_val)],
                callbacks=[
                    lgb.early_stopping(20),
                    lgb.log_evaluation(period=0),
                ]
            )
            
            # Evaluate
            y_pred_proba = model.predict_proba(X_val_scaled)[:, 1]
            auc = roc_auc_score(y_val, y_pred_proba)
            cv_scores.append(auc)
            predictions_cv[val_idx] = y_pred_proba
            
            logger.info(f"   AUC: {auc:.4f}")
            
            models.append(model)
        
        # Overall CV performance
        overall_auc = roc_auc_score(y, predictions_cv)
        logger.info(f"\n✅ CV completed:")
        logger.info(f"   Mean AUC: {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores):.4f})")
        logger.info(f"   Overall AUC: {overall_auc:.4f}")
        
        return models, cv_scores
    
    def train_final_model(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2):
        """
        Train final model on full training set (80/20 split).
        """
        logger.info(f"\n🚀 Training final model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, stratify=y, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = lgb.LGBMClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            num_leaves=31,
            random_state=42,
            verbosity=-1,
            is_unbalanced=True,
        )
        
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            callbacks=[
                lgb.early_stopping(20),
                lgb.log_evaluation(period=0),
            ]
        )
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        auc = roc_auc_score(y_test, y_pred_proba)
        cm = confusion_matrix(y_test, y_pred)
        
        logger.info(f"✅ Final model trained:")
        logger.info(f"   Test AUC: {auc:.4f}")
        logger.info(f"   Confusion matrix:\n{cm}")
        logger.info(f"\n   Classification report:")
        logger.info(classification_report(y_test, y_pred))
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"\n📊 Top 10 features:")
        logger.info(self.feature_importance.head(10).to_string(index=False))
        
        return self.model, auc
    
    def apply_platt_scaling(self, y_val: pd.Series, y_pred_proba: np.ndarray):
        """
        Apply Platt scaling to calibrate probability outputs.
        
        Returns calibration parameters (A, B) for use in production:
        calibrated_prob = 1 / (1 + exp(A * raw_prob + B))
        """
        from scipy.optimize import minimize
        from scipy.special import expit
        
        logger.info("\n📐 Applying Platt scaling for calibration...")
        
        # Clip predictions to avoid numerical issues
        y_pred_proba = np.clip(y_pred_proba, 1e-6, 1 - 1e-6)
        
        def objective(params):
            A, B = params
            # Cross-entropy loss
            predictions = expit(A * y_pred_proba + B)
            return -np.mean(y_val * np.log(predictions) + (1 - y_val) * np.log(1 - predictions))
        
        # Optimize
        result = minimize(objective, x0=[1.0, 0.0], method='Nelder-Mead')
        A, B = result.x
        
        logger.info(f"✅ Platt calibration parameters:")
        logger.info(f"   A = {A:.6f}, B = {B:.6f}")
        
        # Test calibration
        calibrated_proba = expit(A * y_pred_proba + B)
        from sklearn.calibration import calibration_curve
        frac_pos, mean_pred = calibration_curve(y_val, calibrated_proba, n_bins=10)
        
        logger.info(f"✅ Calibration curve computed (10 bins)")
        
        return {'A': float(A), 'B': float(B)}
    
    def save_model(self, model_name: str = 'au_moins_1_but_model.pkl'):
        """Save trained model and scaler."""
        import pickle
        
        model_path = self.output_dir / model_name
        scaler_path = self.output_dir / 'scaler.pkl'
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        logger.info(f"✅ Model saved to {model_path}")
        logger.info(f"✅ Scaler saved to {scaler_path}")


def main():
    """Example: Train model on Phase 1 historical data."""
    
    print("\n" + "=" * 70)
    print("🎯 PHASE 2: ML MODEL TRAINING")
    print("=" * 70 + "\n")
    
    builder = MLModelBuilder(output_dir='models')
    
    # STEP 1: Load historical data
    historical_csv = 'historical_matches.csv'
    try:
        df = builder.load_historical_data(historical_csv)
    except FileNotFoundError:
        logger.error(f"❌ File not found: {historical_csv}")
        logger.error("Run Phase 1 scraper first: python historical_scraper.py")
        return
    
    # STEP 2: Prepare features
    X, y = builder.prepare_features(df)
    
    # STEP 3: Train with K-fold CV
    models_cv, cv_scores = builder.train_with_kfold(X, y, n_splits=5)
    
    # STEP 4: Train final model
    model, test_auc = builder.train_final_model(X, y, test_size=0.2)
    
    # STEP 5: Save model
    builder.save_model('au_moins_1_but_model.pkl')
    
    print("\n" + "=" * 70)
    print("✅ TRAINING COMPLETE")
    print("=" * 70 + "\n")
    print("📊 Summary:")
    print(f"   - CV Mean AUC: {np.mean(cv_scores):.4f}")
    print(f"   - Test AUC: {test_auc:.4f}")
    print(f"   - Model saved to: models/au_moins_1_but_model.pkl")
    print(f"   - Next: Integrate with live prediction pipeline")


if __name__ == "__main__":
    main()
