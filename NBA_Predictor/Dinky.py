import os
import pandas as pd
import torch
from torch import nn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import numpy as np
import random

folder_path = "/Users/harishdukkipati/Downloads/HELLY's_DEVIL_MAGIC/Pacers"
folder_path_1 = "/Users/harishdukkipati/Downloads/HELLY's_DEVIL_MAGIC/Thunder"

dfs = {}
regular_dict = {
    'Tyrese': 'OKC',
    'Myles': 'OKC',
    'Shai': 'IND',
    'Jalen': 'IND',
    'Lu': 'IND',
    'Pascal': 'OKC'
}

post_dict = {
    'Aaron': 'IND',
    'Chet': 'IND',
    'Benedit': 'OKC',
    'Andrew': 'OKC',
    'Alex': 'IND',
    'TJ': 'OKC'
}
pacers_opponent = 'OKC'
thunder_opponent = 'IND'

def weighted_mean(series):
    series = series.apply(safe_numeric)
    weights = np.linspace(0.5, 1.0, len(series))  # earlier games get 0.5, recent games get 1.0
    return np.average(series, weights=weights)


def safe_numeric(x):
    try:
        return float(x)
    except:
        return 0.0


def set_seed(seed=42):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def load_and_clean_csv(filepath):
    """Load CSV, clean up formatting, and sanitize contents."""
    df = pd.read_csv(filepath)

    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    df = df[~df.apply(lambda row: row.astype(str).str.contains("Inactive|Did", case=False).any(), axis=1)]

    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)

    df.fillna(0, inplace=True)

    return df.reset_index(drop=True)



# Load all CSV files with proper header handling
for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):
        filepath = os.path.join(folder_path, filename)
        firstname = filename.split("_")[0]  
        dfs[firstname] = load_and_clean_csv(filepath)

for filename in os.listdir(folder_path_1):
    if filename.endswith(".csv"):
        filepath = os.path.join(folder_path_1, filename)
        firstname = filename.split("_")[0]  
        dfs[firstname] = load_and_clean_csv(filepath)

for name, df in dfs.items():
    df = df[~df.apply(lambda row: row.astype(str).str.contains("Inactive|Did").any(), axis=1)].reset_index(drop=True)
    is_pacer = "IND" in df['Team'].iloc[0]
    df['weight'] = df['Opp'].apply(lambda opp: 2 if (is_pacer and opp == "OKC") or (not is_pacer and opp == "IND") else 1.0)
    df['PLAYER'] = name
    dfs[name] = df

print(dfs['Shai']['PTS'])

# Combine all DataFrames
def convert_minutes(mp):
    """Convert 'MM:SS' format to numeric minutes, defaulting to 0 on errors."""
    parts = mp.split(':')
    if len(parts) == 2:
        minutes = float(parts[0])
        seconds = float(parts[1])
        result = minutes + (seconds / 60)
        return result
    return float(mp)  # Try direct conversion (may be just "0" or "35")

def create_features(df):
    """Create proper numeric features"""
    df = df.copy()
    
    df['MP'] = df['MP'].apply(convert_minutes)
    
    features = df[[
        'MP', 'GS', 'FGA', 'FG', 'FG%', '3PA', '3P%', 
        'FTA', 'FT%', 'ORB', 'DRB', 'PF'
    ]].copy()
    
    # Add rolling stats (past 3 games)
    for stat in target_cols:
        features[f'Last3_{stat}'] = df[stat].rolling(3).mean().shift(1)
    
    # Add opponent indicator (simple version)
    features['vs_OKC'] = (df['Opp'] == 'OKC').astype(int)
    features['vs_IND'] = (df['Opp'] == 'IND').astype(int)
    
    # Fill any remaining NaNs
    features = features.fillna(0)
    
    return features

all_data = pd.concat(dfs.values(), ignore_index=True)

all_indices = np.arange(len(all_data))  

target_cols = ['PTS', 'TRB', 'AST', 'STL', 'BLK', 'TOV', '3P'] 

features = create_features(all_data)
targets = all_data[target_cols]
weights = all_data['weight'] if 'weight' in all_data else pd.Series(1.0, index=all_data.index)

scaler = StandardScaler()
X = scaler.fit_transform(features)

target_scaler = MinMaxScaler()
y = target_scaler.fit_transform(targets.astype(float).values)

w = weights.values

train_idx, val_idx = train_test_split(all_indices, test_size=0.2, random_state=42)

# Create train/val splits for features, targets, and weights
X_train_np, X_val_np = X[train_idx], X[val_idx]
y_train_np, y_val_np = y[train_idx], y[val_idx]
w_train_np, w_val_np = w[train_idx], w[val_idx]

# Convert numpy arrays to torch tensors
X_train = torch.tensor(X_train_np, dtype=torch.float32)
X_val = torch.tensor(X_val_np, dtype=torch.float32)
y_train = torch.tensor(y_train_np, dtype=torch.float32)
y_val = torch.tensor(y_val_np, dtype=torch.float32)
w_train = torch.tensor(w_train_np, dtype=torch.float32)
w_val = torch.tensor(w_val_np, dtype=torch.float32)

class Net(nn.Module):
    def __init__(self, input_dim):
        super(Net, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, len(target_cols)),
        )

    def forward(self, x):
        return self.net(x)

model = Net(X_train.shape[1])
loss_fn = nn.MSELoss(reduction='none') 
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

best_val_loss = float('inf')
patience = 10 
patience_counter = 0

for epoch in range(100):
    model.train()
    optimizer.zero_grad()
    preds = model(X_train)
    loss = loss_fn(preds, y_train)
    
    # Apply weights
    if loss.dim() == 2:
        weighted_loss = (loss * w_train.unsqueeze(1)).mean()
    else:
        weighted_loss = (loss * w_train).mean()
    
    weighted_loss.backward()
    optimizer.step()
    
    # Validation and Haliburton AST print every 10 epochs
    if epoch % 10 == 0:
        model.eval()
        with torch.no_grad():
            val_preds = model(X_val)
            val_loss_raw = loss_fn(val_preds, y_val)
            if val_loss_raw.dim() == 2:
                val_loss = (val_loss_raw * w_val.unsqueeze(1)).mean().item()
            else:
                val_loss = (val_loss_raw * w_val).mean().item()
        
        print(f"Epoch {epoch} | Val Loss: {val_loss:.4f}")
        
        # Get Haliburton indices in validation set
        hali_mask_val = all_data.iloc[val_idx]['PLAYER'] == 'Tyrese'
        hali_val_indices = np.array(val_idx)[hali_mask_val.values]
        
        if len(hali_val_indices) > 0:
            hali_X_val = X[hali_val_indices]
            hali_y_val = y[hali_val_indices]

            hali_X_val_tensor = torch.tensor(hali_X_val, dtype=torch.float32)
            hali_y_val_tensor = torch.tensor(hali_y_val, dtype=torch.float32)

            with torch.no_grad():
                hali_preds = model(hali_X_val_tensor).cpu().numpy()

            hali_preds_unscaled = target_scaler.inverse_transform(hali_preds)
            hali_true_unscaled = target_scaler.inverse_transform(hali_y_val)

            ast_idx = target_cols.index('AST')

            # print("\nHaliburton AST Val Predictions vs True:")
            # for pred_val, true_val in zip(hali_preds_unscaled[:, ast_idx], hali_true_unscaled[:, ast_idx]):
            #    print(f"Predicted: {pred_val:.1f} | True: {true_val:.1f}")
        else:
            print("No Haliburton data in validation set!")
        
        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # You can save model here if you want
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print("Early stopping triggered.")
                break


def predict_player_vs_opponent(model, player_name, opponent, dfs, scaler, target_scaler, target_cols, number):
    """Predict performance for specific player vs NEXT opponent game"""
    if player_name not in dfs:
        available = [k for k in dfs.keys() if player_name.lower() in k.lower()]
        raise ValueError(f"Player not found. Similar names: {available}")
    
    player_df = dfs[player_name].copy()
    
    # Get recent games for calculating current form
    recent_games = player_df.tail(3).copy()

    print("Recent PTS values:", recent_games['PTS'].tolist())
    print(recent_games['MP'])
    
    
    # Create feature vector for next game
    next_game_features = pd.DataFrame({
    'MP': [weighted_mean(recent_games['MP'].apply(convert_minutes))],
    'GS': [weighted_mean(recent_games['GS'])],
    'FGA': [weighted_mean(recent_games['FGA'])],
    'FG': [weighted_mean(recent_games['FG'])],
    'FG%': [weighted_mean(recent_games['FG%'])],
    '3PA': [weighted_mean(recent_games['3PA'])],
    '3P%': [weighted_mean(recent_games['3P%'])],
    'FTA': [weighted_mean(recent_games['FTA'])],
    'FT%': [weighted_mean(recent_games['FT%'])],
    'ORB': [weighted_mean(recent_games['ORB'])],
    'DRB': [weighted_mean(recent_games['DRB'])],
    'PF': [weighted_mean(recent_games['PF'])],
})
    
    # Add rolling stats - use last 3 games for "Last3_" features
    last_3_games = recent_games.tail(3)
    for stat in target_cols:
        # Ensure numeric conversion using safe_numeric or float cast
        values = last_3_games[stat].apply(safe_numeric).astype(float)
        next_game_features[f'Last3_{stat}'] = values.mean()
    
    # Set opponent features
    next_game_features['vs_OKC'] = 1 if opponent == 'OKC' else 0
    next_game_features['vs_IND'] = 1 if opponent == 'IND' else 0
    
    # Fill any NaNs
    print(next_game_features)
    next_game_features = next_game_features.fillna(0)
    
    next_game_features = next_game_features.astype(float)
    # Scale features using the same scaler
    X_pred = scaler.transform(next_game_features)
    X_pred_tensor = torch.tensor(X_pred, dtype=torch.float32)
    
    model.eval()
    with torch.no_grad():
        pred = model(X_pred_tensor).numpy()
        print("\n=== Raw Model Output (scaled) ===")
        print(pred)
        pred = target_scaler.inverse_transform(pred)[0]
        pred = np.clip(pred, a_min=0, a_max=None)
        pred = [round(x) for x in pred]
        print("\n=== Rounded Output ===")
        print(pred)

    return dict(zip(target_cols, pred))

# 7. Make Prediction
try:
    for haliban, opponent in regular_dict.items():
        prediction = predict_player_vs_opponent(model, haliban, opponent, dfs, scaler, target_scaler, target_cols, 70)
        print(f"\nPredicted stats for {haliban} vs {opponent}:")
        for stat, value in prediction.items(): 
            print(f"{stat}: {value:.1f}")
    for dinky, opponent in post_dict.items():
        winky = predict_player_vs_opponent(model, dinky, opponent, dfs, scaler, target_scaler, target_cols, 20)
        print(f"\nPredicted stats for {dinky} vs {opponent}:")
        for stat, value in winky.items():
            print(f"{stat}: {value:.1f}")
            
except ValueError as e:
    print(f"Error: {e}")