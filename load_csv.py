
import pandas as pd
import math
import matplotlib.pyplot as plt


# Его суть такова. Если индекс чистых цен средних ОФЗ (RUGBICP3Y) за последние 3 месяца показал 
# положительную доходность, то берем дальние ОФЗ (индекс RUGBITR10Y). 
# Если отрицательную - то перекладываемся в самые ближние бумаги (индекс RUGBITR1Y).

# Проведем такой же фокус с корпоративными облигациями. 
# В качестве дальних возьмем индекс RUCBTR5YNS, а в качестве ближних RUCBITR1Y. 
# Что касается индекса чистых цен средних облигаций, 
# то здесь попробуем две опции: 
# 1) ориентироваться на RUCBCP3YNS; 
# 2) вместо корпоративных смотреть на динамику ОФЗ RUGBICP3Y.

# С апреля 2019 по ноябрь 2025 такой моментум на корпоративных бондах принес 111,6%, 
# если ориентироваться на RUCBCP3YNS, и 132,2%, 
# если ориентироваться RUGBICP3Y. 
# Индекс корпоративных облигаций RUCBTRNS вырос на 80,6%. 
# Издержки здесь не учтены. 
# Но перекладываний из дальних в ближнее было очень немного, 
# а бид-аск спреды в облигациях из названных выше индексов, в отличие от ВДО, незначительны.


def load_csv_to_dataframe(file_path):
    """
    Loads a CSV file into a pandas DataFrame.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        pandas.DataFrame: The loaded DataFrame.
    """
    try:
        df = pd.read_csv(file_path, index_col='date', parse_dates=True)
        print(f"Successfully loaded {file_path}")
        print("DataFrame head:")
        print(df.head())
        return df
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: The file {file_path} is empty.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def add_calculated_column(df):
    df['state'] = df['RUGBICP3Y.INDX'].gt(df['RUGBICP3Y.INDX'].shift(90)).apply(lambda x: '10Y' if x else '1Y')

def simulate(df: pd.DataFrame, initial_investment=100000) -> tuple[float, int]:
    cumulative: float = 0
    cumulative_list = []
    state: str =  None
    position: int = 0
    invest = initial_investment
    roatations: int = 0
    for index, row in df.iterrows():
        #print(f"Date: {index}, Row Data: {row['state']} {invest}")
        if state is None:
            position = invest / row['RUGBITR1Y.INDX']
            state = '1Y'   
            df.at[index, 'strategy'] = invest     
        else:    
            if row['state'] == '1Y' and state == '10Y':
                invest = position * row['RUGBITR10Y.INDX']
                position = invest / row['RUGBITR1Y.INDX']
                roatations += 1
                state = '1Y'
                df.at[index, 'strategy'] = invest
            elif row['state'] == '10Y' and state == '1Y':
                invest = position * row['RUGBITR1Y.INDX']
                position = invest / row['RUGBITR10Y.INDX']
                roatations += 1
                state = '10Y' 
                df.at[index, 'strategy'] = invest
            
            if state == '1Y':
                invest = position * row['RUGBITR1Y.INDX']    
                df.at[index, 'strategy'] = invest
            elif state == '10Y':
                invest = position * row['RUGBITR10Y.INDX']    
                df.at[index, 'strategy'] = invest
                
    
    cumulative = position * (row['RUGBITR10Y.INDX'] if state == '10Y' else row['RUGBITR1Y.INDX'])
    return (cumulative, roatations)

def toal(df: pd.DataFrame, column_name='RUGBITR10Y.INDX') -> float:
    first_value = df[column_name].iloc[0]
    last_value = df[column_name].iloc[-1]
    return last_value/first_value

def calculate_year_difference(df):
    first_date = df.index[0]
    last_date = df.index[-1]
    diff_days = (last_date - first_date).days
    diff_years = diff_days / 365.25
    return diff_years

def truncate_df(df, from_date, to_date):
    return df.loc[from_date:to_date]

def plot_df(df):
    fig, ax = plt.subplots()
    ax.plot(df.index, df['RUGBITR1Y_norm'], color='blue', label='RUGBITR1Y_norm')
    ax.plot(df.index, df['RUGBITR10Y_norm'], color='orange', label='RUGBITR10Y_norm')
    current_color = 'black' if df['state'].iloc[0] == '10Y' else 'lightgreen'
    start_idx = 0
    strategy_label_added = False
    for i in range(1, len(df)):
        if df['state'].iloc[i] != df['state'].iloc[i-1]:
            label = 'Strategy' if not strategy_label_added else None
            ax.plot(df.index[start_idx:i], df['strategy_norm'].iloc[start_idx:i], color=current_color, label=label)
            if label:
                strategy_label_added = True
            current_color = 'lightgreen' if df['state'].iloc[i] == '1Y' else 'black'
            start_idx = i
    label = 'Strategy' if not strategy_label_added else None
    ax.plot(df.index[start_idx:], df['strategy_norm'].iloc[start_idx:], color=current_color, label=label)
    plt.title('Normalized Indices and Strategy Over Time')
    plt.xlabel('Date')
    plt.ylabel('Normalized Value')
    plt.legend()
    plt.savefig('plot.png')
    

def normalize_columns(df):
    df['RUGBITR1Y_norm'] = df['RUGBITR1Y.INDX'] / df['RUGBITR1Y.INDX'].iloc[0] * 100
    df['RUGBITR10Y_norm'] = df['RUGBITR10Y.INDX'] / df['RUGBITR10Y.INDX'].iloc[0] * 100
    
    
def normalize_strategy(df):
    df['strategy_norm'] = df['strategy'] / df['strategy'].iloc[0] * 100    

if __name__ == "__main__":
    
    file_paths = ["files/RUGBICP3Y.INDX", "files/RUGBITR1Y.INDX", "files/RUGBITR10Y.INDX"]
    all_data = []

    for file_path in file_paths:
        df = load_csv_to_dataframe(file_path)
        if df is not None:
            all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, axis=1)
        print("\nAll CSVs loaded into a single DataFrame:")
        print(combined_df.head())
        print("\nCombined DataFrame info:")
        combined_df.info()

        # Truncate to 2015-2020
        #2010-12-30
        #combined_df = truncate_df(combined_df, '2011-01-01', '2025-10-30')
        combined_df = truncate_df(combined_df, '2020-01-01', '2026-01-01')
        print("\nAfter truncation:")
        print(combined_df.head())
        print(combined_df.tail())

        add_calculated_column(combined_df)
        print("\nDataFrame with new column:")
        print(combined_df.head())
        print("\nDataFrame with new column info:")
        combined_df.info()

        normalize_columns(combined_df)
        print("\nDataFrame with normalized columns:")
        print(combined_df[['RUGBITR1Y_norm', 'RUGBITR10Y_norm']].head())

        initial_investment=100000

        result = simulate(combined_df, initial_investment=initial_investment)

        normalize_strategy(combined_df)

        print(combined_df.head())

        print(f"\nSimulation result: {result[0]}, Rotations: {result[1] }")

        total_value_1 = toal(combined_df, 'RUGBITR1Y.INDX')
        total_value_10 = toal(combined_df, 'RUGBITR10Y.INDX')
        print(f"\nTotal value change for RUGBITR1Y.INDX: {total_value_1}")
        print(f"Total value change for RUGBITR10Y.INDX: {total_value_10}")

        total_years = calculate_year_difference(combined_df)
        print(f"Total years in dataset: {total_years}")

        print(f"RUGBITR1Y per year: { math.pow(total_value_1, 1/total_years) } ")
        print(f"RUGBITR10Y per year: { math.pow(total_value_10, 1/total_years) } ")
        strategy_persent = result[0] / initial_investment
        print(f"Strategy total return: { strategy_persent } ")
        print(f"Strategy per year: { math.pow(strategy_persent, 1/total_years) } ")

        plot_df(combined_df)



