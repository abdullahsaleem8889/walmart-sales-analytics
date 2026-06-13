"""
Dedicated ML Model Training Script
====================================================================

Standalone training pipeline for Walmart Sales Forecasting models.
This script handles all ML training logic separately from the Flask backend.

Components:
  |- Data Loading & Preprocessing
  |- Feature Engineering
  |- Model Training (XGBoost, LightGBM, Random Forest)
  |- Hyperparameter Tuning (Optuna)
  |- Ensemble Predictions
  |- Model Evaluation
  +- Model Serialization

Usage:
    python train_models.py [--mode {full|quick|xgboost|lightgbm|random_forest}] [--test]

Author: ML Engineering Team
Version: 1.0
Date: March 29, 2026
"""

import os
import sys
import json
import pickle
import argparse
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
import lightgbm as lgb

try:
    import optuna
    from optuna.samplers import TPESampler
    from optuna.pruners import MedianPruner
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    print("[WARNING]  Optuna not available - will use GridSearchCV for tuning")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("[WARNING]  Prophet not available - skipping Prophet model")

class TrainingConfig:
    """Training configuration and constants."""

    DATA_PATH = Path(__file__).parent.parent                      
    MODELS_PATH = DATA_PATH / "models"
    LOGS_PATH = DATA_PATH / "logs"

    MODELS_PATH.mkdir(exist_ok=True)
    LOGS_PATH.mkdir(exist_ok=True)

    RANDOM_STATE = 42
    TEST_SIZE = 0.2
    CV_SPLITS = 3

    OPTUNA_TRIALS = 30
    OPTUNA_TIMEOUT = 3600          

    XGBOOST_PARAMS = {
        'n_estimators': 200,
        'learning_rate': 0.1,
        'max_depth': 6,
        'min_child_weight': 1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': RANDOM_STATE,
        'n_jobs': -1,
        'verbosity': 0
    }

    LIGHTGBM_PARAMS = {
        'n_estimators': 200,
        'learning_rate': 0.1,
        'max_depth': 6,
        'num_leaves': 31,
        'random_state': RANDOM_STATE,
        'n_jobs': -1,
        'verbose': -1
    }

    RANDOM_FOREST_PARAMS = {
        'n_estimators': 200,
        'max_depth': 20,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': RANDOM_STATE,
        'n_jobs': -1,
        'verbose': 0
    }

class DataProcessor:
    """Handle data loading, preprocessing, and feature engineering."""

    def __init__(self, data_path=None):
        """Initialize data processor."""
        self.data_path = data_path or TrainingConfig.DATA_PATH
        self.full_data = None
        self.X = None
        self.y = None
        self.scaler = StandardScaler()

    def load_data(self):
        """Load and merge all datasets."""

        print("\n" + "="*70)
        print("[INFO] LOADING DATA")
        print("="*70)

        try:

            train_path = self.data_path / 'data' / 'train.csv'
            stores_path = self.data_path / 'data' / 'stores.csv'
            features_path = self.data_path / 'data' / 'features.csv'

            if not all([train_path.exists(), stores_path.exists(), features_path.exists()]):
                raise FileNotFoundError("Missing required CSV files")

            train_data = pd.read_csv(train_path)
            stores_data = pd.read_csv(stores_path)
            features_data = pd.read_csv(features_path)

            print(f"[OK] Loaded train.csv: {len(train_data)} rows")
            print(f"[OK] Loaded stores.csv: {len(stores_data)} rows")
            print(f"[OK] Loaded features.csv: {len(features_data)} rows")

            train_data['Date'] = pd.to_datetime(train_data['Date'])
            features_data['Date'] = pd.to_datetime(features_data['Date'])

            full_data = train_data.merge(
                features_data, 
                on=['Store', 'Date'], 
                how='left',
                suffixes=('_train', '_features')
            )
            full_data = full_data.merge(stores_data, on='Store', how='left')

            if 'IsHoliday_train' in full_data.columns:
                full_data['IsHoliday'] = full_data['IsHoliday_train']
                full_data = full_data.drop(
                    columns=['IsHoliday_train', 'IsHoliday_features'], 
                    errors='ignore'
                )

            full_data['Weekly_Sales'] = pd.to_numeric(full_data['Weekly_Sales'], errors='coerce')
            full_data = full_data.dropna(subset=['Weekly_Sales'])

            self.full_data = full_data.sort_values('Date').reset_index(drop=True)

            print(f"\n[OK] Merged dataset shape: {self.full_data.shape}")
            print(f"[DATE] Date range: {self.full_data['Date'].min()} to {self.full_data['Date'].max()}")
            print(f"[OK] Data loading successful!\n")

            return self.full_data

        except Exception as e:
            print(f"[ERROR] Error loading data: {e}")
            raise

    def prepare_feature_matrix(self):
        """Prepare basic Feature Matrix (X) and Target Variable (y)."""

        print("="*70)
        print("[INFO] PREPARING FEATURE MATRIX & TARGET VARIABLE")
        print("="*70)

        try:
            data = self.full_data.copy()

            print("\n[STEP] Step 1: Extract Core Features")
            print("   |- Store ID: Store identifier")
            print("   |- Department ID: Department identifier")
            print("   |- Temperature: Environmental temperature")
            print("   |- Fuel Price: Fuel price indicator")
            print("   |- CPI: Consumer Price Index")
            print("   +- IsHoliday: Holiday flag (0=No, 1=Yes)")

            core_features = ['Store', 'Dept', 'Temperature', 'Fuel_Price', 'CPI', 'IsHoliday']

            available_core = [col for col in core_features if col in data.columns]

            missing = set(core_features) - set(available_core)
            if missing:
                print(f"   [WARNING]  Missing features: {missing}")

            X_core = data[available_core].copy()

            print(f"\n[OK] Core Features Selected: {len(available_core)} features")
            print(f"   {', '.join(available_core)}")

            print(f"\n[STEP] Step 2: Extract Target Variable")
            print("   +- Weekly_Sales: Sales value to predict")

            y = data['Weekly_Sales'].copy()

            print(f"\n[OK] Target Variable Selected: Weekly_Sales")
            print(f"   Min: ${y.min():,.2f}")
            print(f"   Max: ${y.max():,.2f}")
            print(f"   Mean: ${y.mean():,.2f}")
            print(f"   Std: ${y.std():,.2f}")

            print(f"\n[STEP] Step 3: Data Quality Validation")
            print(f"   Total rows: {len(X_core)}")
            print(f"   Missing values in X: {X_core.isnull().sum().sum()}")
            print(f"   Missing values in y: {y.isnull().sum()}")

            X_core = X_core.fillna(X_core.mean(numeric_only=True))
            y = y.fillna(y.mean())

            print(f"   [OK] Missing values handled")

            print(f"\n[STEP] Step 4: Feature Matrix Shape")
            print(f"   X shape (samples  features): {X_core.shape}")
            print(f"   y shape (samples): {y.shape}")

            self.X_core = X_core
            self.y = y

            print(f"\n[OK] Feature Matrix & Target Variable prepared!\n")

            return X_core, y

        except Exception as e:
            print(f"[ERROR] Error preparing feature matrix: {e}")
            raise

    def prepare_features(self):
        """Prepare features for modeling (with advanced feature engineering)."""

        print("="*70)
        print("[FEAT] ADVANCED FEATURE ENGINEERING")
        print("="*70)

        try:
            data = self.full_data.copy()

            print("\n[STEP] Step 1: Starting with core features (Store, Dept, Temperature, etc.)")

            print("[STEP] Step 2: Extracting temporal features...")
            data['Year'] = data['Date'].dt.year
            data['Month'] = data['Date'].dt.month
            data['Week'] = data['Date'].dt.isocalendar().week
            data['DayOfWeek'] = data['Date'].dt.dayofweek
            print("   [OK] Temporal features: Year, Month, Week, DayOfWeek")

            print("[STEP] Step 3: Engineering lag features...")
            data = data.sort_values(['Store', 'Dept', 'Date']).reset_index(drop=True)

            for lag in [1, 4, 12, 26, 52]:
                data[f'Sales_Lag_{lag}'] = data.groupby(
                    ['Store', 'Dept']
                )['Weekly_Sales'].shift(lag)
            print("   [OK] Lag features: 1-week, 4-week, 12-week, 26-week, 52-week")

            print("[STEP] Step 4: Computing rolling averages...")
            for window in [4, 12, 26]:
                data[f'Sales_MA_{window}'] = data.groupby(
                    ['Store', 'Dept']
                )['Weekly_Sales'].transform(
                    lambda x: x.rolling(window=window, min_periods=1).mean()
                )
            print("   [OK] Moving averages: 4-week, 12-week, 26-week")

            print("[STEP] Step 5: Computing exponential moving average...")
            data['Sales_EMA_12'] = data.groupby(
                ['Store', 'Dept']
            )['Weekly_Sales'].transform(
                lambda x: x.ewm(span=12, adjust=False).mean()
            )
            print("   [OK] EMA: 12-week exponential")

            print("[STEP] Step 6: Handling missing values...")
            data = data.fillna(data.mean(numeric_only=True))
            print("   [OK] Filled with mean values")

            feature_cols = [
                'Store', 'Dept', 'Type', 'Size',
                'Temperature', 'Fuel_Price', 'CPI', 'Unemployment', 'IsHoliday',
                'Year', 'Month', 'Week', 'DayOfWeek',
                'Sales_Lag_1', 'Sales_Lag_4', 'Sales_Lag_12', 'Sales_Lag_26', 'Sales_Lag_52',
                'Sales_MA_4', 'Sales_MA_12', 'Sales_MA_26',
                'Sales_EMA_12'
            ]

            available_cols = [col for col in feature_cols if col in data.columns]
            X = data[available_cols].copy()
            y = data['Weekly_Sales'].copy()

            if 'Type' in X.columns:
                X['Type'] = pd.Categorical(X['Type']).codes

            print("[STEP] Step 7: Scaling features...")
            X_scaled = self.scaler.fit_transform(X)
            X_scaled = pd.DataFrame(X_scaled, columns=available_cols)
            print("   [OK] StandardScaler applied")

            self.X = X_scaled
            self.y = y

            print(f"\n[OK] Advanced Feature Engineering Complete!")
            print(f"   Total features engineered: {len(available_cols)}")
            print(f"   Feature breakdown:")
            print(f"      Core features: 6 (Store, Dept, Temp, Fuel, CPI, Holiday)")
            print(f"      Store features: 2 (Type, Size)")
            print(f"      Temporal features: 4 (Year, Month, Week, DayOfWeek)")
            print(f"      Lag features: 5 (1, 4, 12, 26, 52-week)")
            print(f"      Rolling averages: 3 (4, 12, 26-week)")
            print(f"      EMA features: 1 (12-week)")
            print(f"   Total samples: {len(X_scaled)}\n")

            return X_scaled, y

        except Exception as e:
            print(f"[ERROR] Error in feature engineering: {e}")
            raise

class ModelTrainer:
    """Train and tune ML models."""

    def __init__(self, X, y, scaler=None, config=None):
        """Initialize model trainer."""
        self.X = X
        self.y = y
        self.scaler = scaler                                  
        self.config = config or TrainingConfig()
        self.models = {}
        self.results = {}
        self.tscv = TimeSeriesSplit(n_splits=self.config.CV_SPLITS)

    def train_xgboost(self, tune=True):
        """Train XGBoost model with optional hyperparameter tuning."""

        print("\n" + "="*70)
        print("[TRAIN] TRAINING XGBOOST")
        print("="*70)

        try:
            if tune and OPTUNA_AVAILABLE:
                print("[SEARCH] Running Optuna hyperparameter tuning (30 trials)...")
                best_params = self._optuna_xgboost()
            else:
                print("Using default XGBoost parameters...")
                best_params = self.config.XGBOOST_PARAMS

            model = xgb.XGBRegressor(**best_params)
            model.fit(self.X, self.y, verbose=False)

            self.models['xgboost'] = model

            y_pred = model.predict(self.X)
            rmse = np.sqrt(mean_squared_error(self.y, y_pred))
            mae = mean_absolute_error(self.y, y_pred)
            r2 = r2_score(self.y, y_pred)

            self.results['xgboost'] = {'rmse': rmse, 'mae': mae, 'r2': r2}

            print(f"[OK] XGBoost trained!")
            print(f"   RMSE: {rmse:.2f}")
            print(f"   MAE: {mae:.2f}")
            print(f"   R: {r2:.4f}\n")

            return model

        except Exception as e:
            print(f"[ERROR] Error training XGBoost: {e}")
            raise

    def train_lightgbm(self, tune=True):
        """Train LightGBM model with optional hyperparameter tuning."""

        print("="*70)
        print("[TRAIN] TRAINING LIGHTGBM")
        print("="*70)

        try:
            if tune and OPTUNA_AVAILABLE:
                print("[SEARCH] Running Optuna hyperparameter tuning (30 trials)...")
                best_params = self._optuna_lightgbm()
            else:
                print("Using default LightGBM parameters...")
                best_params = self.config.LIGHTGBM_PARAMS

            model = lgb.LGBMRegressor(**best_params)
            model.fit(self.X, self.y)

            self.models['lightgbm'] = model

            y_pred = model.predict(self.X)
            rmse = np.sqrt(mean_squared_error(self.y, y_pred))
            mae = mean_absolute_error(self.y, y_pred)
            r2 = r2_score(self.y, y_pred)

            self.results['lightgbm'] = {'rmse': rmse, 'mae': mae, 'r2': r2}

            print(f"[OK] LightGBM trained!")
            print(f"   RMSE: {rmse:.2f}")
            print(f"   MAE: {mae:.2f}")
            print(f"   R: {r2:.4f}\n")

            return model

        except Exception as e:
            print(f"[ERROR] Error training LightGBM: {e}")
            raise

    def train_random_forest(self, tune=False):
        """Train Random Forest Regressor with optional hyperparameter tuning."""

        print("="*70)
        print("[TRAIN] TRAINING RANDOM FOREST REGRESSOR")
        print("="*70)

        try:
            if tune and OPTUNA_AVAILABLE:
                print("[SEARCH] Running Optuna hyperparameter tuning (30 trials)...")
                best_params = self._optuna_random_forest()
            else:
                print("Using default Random Forest parameters...")
                best_params = self.config.RANDOM_FOREST_PARAMS

            model = RandomForestRegressor(**best_params)
            model.fit(self.X, self.y)

            self.models['random_forest'] = model

            y_pred = model.predict(self.X)
            rmse = np.sqrt(mean_squared_error(self.y, y_pred))
            mae = mean_absolute_error(self.y, y_pred)
            r2 = r2_score(self.y, y_pred)

            self.results['random_forest'] = {'rmse': rmse, 'mae': mae, 'r2': r2}

            print(f"[OK] Random Forest trained!")
            print(f"   RMSE: {rmse:.2f}")
            print(f"   MAE: {mae:.2f}")
            print(f"   R: {r2:.4f}\n")

            return model

        except Exception as e:
            print(f"[ERROR] Error training Random Forest: {e}")
            raise

    def _optuna_random_forest(self):
        """Optuna optimization for Random Forest."""

        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                'max_depth': trial.suggest_int('max_depth', 5, 30),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                'max_features': trial.suggest_choice('max_features', ['sqrt', 'log2']),
                'random_state': self.config.RANDOM_STATE,
                'n_jobs': -1,
                'verbose': 0
            }

            model = RandomForestRegressor(**params)
            scores = []

            for train_idx, val_idx in self.tscv.split(self.X):
                X_train, X_val = self.X.iloc[train_idx], self.X.iloc[val_idx]
                y_train, y_val = self.y.iloc[train_idx], self.y.iloc[val_idx]

                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)
                rmse = np.sqrt(mean_squared_error(y_val, y_pred))
                scores.append(rmse)

            return np.mean(scores)

        sampler = TPESampler(seed=self.config.RANDOM_STATE)
        study = optuna.create_study(sampler=sampler, direction='minimize')
        study.optimize(objective, n_trials=self.config.OPTUNA_TRIALS, show_progress_bar=True)

        print(f"[OK] Best RMSE: {study.best_value:.2f}")
        print(f"   Best Hyperparameters: {study.best_params}\n")

        return study.best_params

    def _optuna_xgboost(self):
        """Optuna optimization for XGBoost."""

        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'max_depth': trial.suggest_int('max_depth', 3, 12),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'subsample': trial.suggest_float('subsample', 0.5, 1),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1),
                'random_state': self.config.RANDOM_STATE,
                'n_jobs': -1,
                'verbosity': 0
            }

            model = xgb.XGBRegressor(**params)
            scores = []

            for train_idx, val_idx in self.tscv.split(self.X):
                X_train, X_val = self.X.iloc[train_idx], self.X.iloc[val_idx]
                y_train, y_val = self.y.iloc[train_idx], self.y.iloc[val_idx]

                model.fit(X_train, y_train, verbose=False)
                y_pred = model.predict(X_val)
                rmse = np.sqrt(mean_squared_error(y_val, y_pred))
                scores.append(rmse)

            return np.mean(scores)

        sampler = TPESampler(seed=self.config.RANDOM_STATE)
        study = optuna.create_study(sampler=sampler, direction='minimize')
        study.optimize(objective, n_trials=self.config.OPTUNA_TRIALS, show_progress_bar=True)

        print(f"[OK] Best RMSE: {study.best_value:.2f}")
        print(f"   Best Hyperparameters: {study.best_params}\n")

        return study.best_params

    def _optuna_lightgbm(self):
        """Optuna optimization for LightGBM."""

        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'max_depth': trial.suggest_int('max_depth', 3, 12),
                'num_leaves': trial.suggest_int('num_leaves', 20, 100),
                'subsample': trial.suggest_float('subsample', 0.5, 1),
                'random_state': self.config.RANDOM_STATE,
                'n_jobs': -1,
                'verbose': -1
            }

            model = lgb.LGBMRegressor(**params)
            scores = []

            for train_idx, val_idx in self.tscv.split(self.X):
                X_train, X_val = self.X.iloc[train_idx], self.X.iloc[val_idx]
                y_train, y_val = self.y.iloc[train_idx], self.y.iloc[val_idx]

                model.fit(X_train, y_train, verbose=False)
                y_pred = model.predict(X_val)
                rmse = np.sqrt(mean_squared_error(y_val, y_pred))
                scores.append(rmse)

            return np.mean(scores)

        sampler = TPESampler(seed=self.config.RANDOM_STATE)
        study = optuna.create_study(sampler=sampler, direction='minimize')
        study.optimize(objective, n_trials=self.config.OPTUNA_TRIALS, show_progress_bar=True)

        print(f"[OK] Best RMSE: {study.best_value:.2f}")
        print(f"   Best Hyperparameters: {study.best_params}\n")

        return study.best_params

    def save_models(self, save_to_root=True):
        """Save trained models to disk using joblib serialization."""

        print("="*70)
        print("[SAVE] SAVING MODELS - JOBLIB SERIALIZATION")
        print("="*70)

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            models_dir = TrainingConfig.MODELS_PATH / timestamp
            models_dir.mkdir(exist_ok=True)

            for name, model in self.models.items():
                model_path = models_dir / f"{name}_model.pkl"
                joblib.dump(model, model_path)
                print(f"[OK] Saved {name} model: {model_path}")

            scaler_path = models_dir / "scaler.pkl"
            joblib.dump(self.scaler, scaler_path)
            print(f"[OK] Saved scaler: {scaler_path}")

            results_path = models_dir / "results.json"
            with open(results_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"[OK] Saved results: {results_path}")

            try:
                latest_dir = TrainingConfig.MODELS_PATH / "latest"
                if latest_dir.exists() or latest_dir.is_symlink():
                    latest_dir.unlink()
                latest_dir.symlink_to(models_dir)
                print(f"[OK] Updated 'latest' symlink: {latest_dir}")
            except (OSError, PermissionError):
                print(f"  Skipped symlink (requires admin privileges on Windows)")

            if save_to_root:
                print(f"\n[STEP] Exporting Primary Model to Project Root")

                best_model_name = max(self.results, key=lambda x: self.results[x]['r2'])
                best_model = self.models[best_model_name]
                best_r2 = self.results[best_model_name]['r2']

                root_model_path = TrainingConfig.DATA_PATH / "models" / "demand_model.pkl"
                joblib.dump(best_model, root_model_path)
                print(f"   [OK] Saved primary model: {root_model_path}")
                print(f"      Model Type: {best_model_name.upper()}")
                print(f"      R Score: {best_r2:.4f}")

                root_scaler_path = TrainingConfig.DATA_PATH / "models" / "model_scaler.pkl"
                joblib.dump(self.scaler, root_scaler_path)
                print(f"   [OK] Saved scaler: {root_scaler_path}")

                model_metadata = {
                    'timestamp': timestamp,
                    'primary_model': best_model_name,
                    'performance_metrics': self.results,
                    'best_model_r2': best_r2,
                    'total_features': self.X.shape[1],
                    'total_samples': len(self.X),
                    'scaler_path': str(root_scaler_path),
                    'model_path': str(root_model_path)
                }

                root_metadata_path = TrainingConfig.DATA_PATH / "models" / "model_metadata.json"
                with open(root_metadata_path, 'w') as f:
                    json.dump(model_metadata, f, indent=2)
                print(f"   [OK] Saved metadata: {root_metadata_path}\n")

                return root_model_path, root_scaler_path, models_dir

            return models_dir

        except Exception as e:
            print(f"[ERROR] Error saving models: {e}")
            raise

def train_pipeline(mode='full', test=False):
    """Execute complete training pipeline."""

    print("\n" + "="*70)
    print("="*70)
    print("  WALMART SALES FORECASTING - MODEL TRAINING PIPELINE".center(70))
    print(f"  Mode: {mode.upper()} | Test: {test}".center(70))
    print("="*70)
    print("="*70)

    try:

        processor = DataProcessor()
        processor.load_data()

        X_core, y_core = processor.prepare_feature_matrix()

        X, y = processor.prepare_features()

        trainer = ModelTrainer(X, y, scaler=processor.scaler)

        if mode in ['full', 'all']:
            trainer.train_xgboost(tune=True)
            trainer.train_lightgbm(tune=True)
            trainer.train_random_forest(tune=False)
        elif mode == 'quick':
            trainer.train_xgboost(tune=False)
            trainer.train_lightgbm(tune=False)
            trainer.train_random_forest(tune=False)
        elif mode == 'xgboost':
            trainer.train_xgboost(tune=True)
        elif mode == 'lightgbm':
            trainer.train_lightgbm(tune=True)
        elif mode == 'random_forest':
            trainer.train_random_forest(tune=False)

        print("="*70)
        print("[INFO] TRAINING SUMMARY")
        print("="*70)

        for model_name, metrics in trainer.results.items():
            print(f"\n{model_name.upper()}:")
            for metric, value in metrics.items():
                print(f"  {metric.upper()}: {value:.4f}")

        if not test:
            model_paths = trainer.save_models(save_to_root=True)
            if isinstance(model_paths, tuple):
                root_model_path, root_scaler_path, versioned_dir = model_paths
                print(f"\n" + "="*70)
                print(" MODEL EXPORT SUMMARY")
                print("="*70)
                print(f"\nPrimary Model (Project Root):")
                print(f"   {root_model_path.name}: {root_model_path}")
                print(f"   {root_scaler_path.name}: {root_scaler_path}")
                print(f"\nVersioned Models (Archive):")
                print(f"   {versioned_dir}")
            else:
                print(f"\n[OK] Models saved to: {model_paths}")
        else:
            print("\n  Skipping model save (TEST MODE)")

        print("\n" + "="*70)
        print("[OK] TRAINING COMPLETED SUCCESSFULLY!")
        print("="*70 + "\n")

        return trainer.models, trainer.results

    except Exception as e:
        print(f"\n[ERROR] Training pipeline failed: {e}")
        raise

def load_trained_model(model_path=None, scaler_path=None):
    """Load trained model and scaler from disk."""

    if model_path is None:
        model_path = TrainingConfig.DATA_PATH / "demand_model.pkl"
    if scaler_path is None:
        scaler_path = TrainingConfig.DATA_PATH / "model_scaler.pkl"

    try:

        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        model = joblib.load(model_path)
        print(f"[OK] Loaded model: {model_path}")

        scaler = None
        if Path(scaler_path).exists():
            scaler = joblib.load(scaler_path)
            print(f"[OK] Loaded scaler: {scaler_path}")

        return model, scaler

    except Exception as e:
        print(f"[ERROR] Error loading model: {e}")
        raise

def load_model_metadata(metadata_path=None):
    """Load model metadata."""

    if metadata_path is None:
        metadata_path = TrainingConfig.DATA_PATH / "model_metadata.json"

    try:
        if not Path(metadata_path).exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        print(f"[OK] Loaded model metadata:")
        print(f"   Primary Model: {metadata['primary_model'].upper()}")
        print(f"   R Score: {metadata['best_model_r2']:.4f}")
        print(f"   Features: {metadata['total_features']}")
        print(f"   Training Samples: {metadata['total_samples']:,}")
        print(f"   Timestamp: {metadata['timestamp']}\n")

        return metadata

    except Exception as e:
        print(f"[ERROR] Error loading metadata: {e}")
        raise

def main():
    """Command-line interface for training."""

    parser = argparse.ArgumentParser(
        description='Train Walmart Sales Forecasting models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Training modes
  python train_models.py                    # Full training (XGBoost + LightGBM + RF)
  python train_models.py --mode quick       # Quick training without tuning
  python train_models.py --mode random_forest  # Random Forest only
  python train_models.py --test             # Test mode (no model save)

  # Using trained model in Python
  from train_models import load_trained_model, load_model_metadata

  model, scaler = load_trained_model()
  metadata = load_model_metadata()
  predictions = model.predict(X_new)
        """
    )

    parser.add_argument(
        '--mode',
        choices=['full', 'quick', 'xgboost', 'lightgbm', 'random_forest'],
        default='full',
        help='Training mode (default: full)'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (no model save)'
    )

    args = parser.parse_args()

    train_pipeline(mode=args.mode, test=args.test)

if __name__ == '__main__':
    main()
