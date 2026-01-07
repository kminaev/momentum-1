import pandas as pd
import math
import matplotlib.pyplot as plt

def load_csv(file_path):
    """Load CSV into DataFrame with date index."""
    df = pd.read_csv(file_path, index_col='date', parse_dates=True)
    return df

def main():
    # Load data
    rugbicp3y = load_csv('files/RUGBICP3Y.INDX')
    rugbitr1y = load_csv('files/RUGBITR1Y.INDX')
    rugbitr10y = load_csv('files/RUGBITR10Y.INDX')

    # Combine into single DataFrame
    combined = pd.concat([rugbicp3y, rugbitr1y, rugbitr10y], axis=1, join='inner')

    # Truncate to 2020 onwards for simulation
    combined = combined.loc['2020-01-01':'2025-12-31']

    # Calculate 3-month return for RUGBICP3Y (90 business days approx 3 months)
    combined['return_3m'] = (combined['RUGBICP3Y.INDX'] / combined['RUGBICP3Y.INDX'].shift(90) - 1)

    # Signal: '10Y' if positive return, else '1Y'
    combined['signal'] = combined['return_3m'].apply(lambda x: '10Y' if x > 0 else '1Y')

    # Simulation
    initial_investment = 1000000
    position = 0  # number of units
    current_state = None
    rotations = 0
    portfolio_values = []

    for index, row in combined.iterrows():
        signal = row['signal']
        price_1y = row['RUGBITR1Y.INDX']
        price_10y = row['RUGBITR10Y.INDX']

        if current_state is None:
            # Initial investment in 1Y
            position = initial_investment / price_1y
            current_state = '1Y'
            portfolio_value = initial_investment
        else:
            if signal != current_state:
                # Switch position
                if current_state == '1Y':
                    # Sell 1Y, buy 10Y
                    cash = position * price_1y
                    position = cash / price_10y
                    current_state = '10Y'
                else:
                    # Sell 10Y, buy 1Y
                    cash = position * price_10y
                    position = cash / price_1y
                    current_state = '1Y'
                rotations += 1
            # Update portfolio value
            if current_state == '1Y':
                portfolio_value = position * price_1y
            else:
                portfolio_value = position * price_10y

        portfolio_values.append(portfolio_value)

    combined['portfolio'] = portfolio_values

    # Final results
    final_value = portfolio_values[-1]
    total_return = final_value / initial_investment - 1
    years = (combined.index[-1] - combined.index[0]).days / 365.25
    annualized_return = (final_value / initial_investment) ** (1 / years) - 1

    # Buy and hold RUGBITR1Y
    buy_hold_1y_value = initial_investment * combined['RUGBITR1Y.INDX'].iloc[-1] / combined['RUGBITR1Y.INDX'].iloc[0]
    buy_hold_1y_return = buy_hold_1y_value / initial_investment - 1
    buy_hold_1y_annual = (buy_hold_1y_value / initial_investment) ** (1 / years) - 1

    # Buy and hold RUGBITR10Y
    buy_hold_10y_value = initial_investment * combined['RUGBITR10Y.INDX'].iloc[-1] / combined['RUGBITR10Y.INDX'].iloc[0]
    buy_hold_10y_return = buy_hold_10y_value / initial_investment - 1
    buy_hold_10y_annual = (buy_hold_10y_value / initial_investment) ** (1 / years) - 1

    print(f"Initial Investment: {initial_investment}")
    print(f"Period: {combined.index[0]} to {combined.index[-1]} ({years:.2f} years)")
    print()
    print("Momentum Strategy:")
    print(f"  Final Portfolio Value: {final_value:.2f}")
    print(f"  Total Return: {total_return:.4%}")
    print(f"  Annualized Return: {annualized_return:.4%}")
    print(f"  Number of Rotations: {rotations}")
    print()
    print("Buy and Hold RUGBITR1Y:")
    print(f"  Final Value: {buy_hold_1y_value:.2f}")
    print(f"  Total Return: {buy_hold_1y_return:.4%}")
    print(f"  Annualized Return: {buy_hold_1y_annual:.4%}")
    print()
    print("Buy and Hold RUGBITR10Y:")
    print(f"  Final Value: {buy_hold_10y_value:.2f}")
    print(f"  Total Return: {buy_hold_10y_return:.4%}")
    print(f"  Annualized Return: {buy_hold_10y_annual:.4%}")

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(combined.index, combined['portfolio'] / initial_investment * 100, label='Momentum Strategy', color='blue')
    ax.plot(combined.index, combined['RUGBITR1Y.INDX'] / combined['RUGBITR1Y.INDX'].iloc[0] * 100, label='Buy & Hold RUGBITR1Y', color='green', alpha=0.7)
    ax.plot(combined.index, combined['RUGBITR10Y.INDX'] / combined['RUGBITR10Y.INDX'].iloc[0] * 100, label='Buy & Hold RUGBITR10Y', color='orange', alpha=0.7)
    ax.set_title('Momentum Strategy vs Buy-and-Hold Benchmarks')
    ax.set_xlabel('Date')
    ax.set_ylabel('Normalized Value (%)')
    ax.legend()
    plt.savefig('momentum_plot.png')
    #plt.show()

if __name__ == "__main__":
    main()