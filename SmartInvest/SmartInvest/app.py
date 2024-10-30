from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)

# Load the mutual fund dataset
data = pd.read_csv('comprehensive_mutual_funds_data.csv')

# Function to compare selected fund(s)
def compare_funds(fund_names):
    if len(fund_names) == 1:
        selected_fund_name = fund_names[0]
        selected_fund_data = data[data['scheme_name'] == selected_fund_name]

        if selected_fund_data.empty:
            return None, "Selected fund not found."

        fund_category = selected_fund_data['category'].values[0]
        other_funds = data[(data['category'] == fund_category) & (data['scheme_name'] != selected_fund_name)]

        if len(other_funds) < 2:
            return None, "Not enough funds in the category to compare."
        
        random_funds = other_funds.sample(n=2, random_state=42)
        funds_to_compare = pd.concat([selected_fund_data, random_funds])
    elif len(fund_names) == 2:
        fund_data = []
        for fund_name in fund_names:
            fund_data_single = data[data['scheme_name'] == fund_name]
            if fund_data_single.empty:
                return None, f"Fund '{fund_name}' not found."
            fund_data.append(fund_data_single)
        funds_to_compare = pd.concat(fund_data)
    else:
        return None, "Please provide either one or two fund names."

    comparison = funds_to_compare[['scheme_name', 'returns_1yr', 'sd', 'sortino', 'expense_ratio']]
    best_fund = comparison.loc[comparison['returns_1yr'].idxmax()]

    # Create the plot
    plt.figure(figsize=(12, 6))
    sns.barplot(data=comparison, x='scheme_name', y='returns_1yr', color='blue', alpha=0.6)
    plt.axhline(y=best_fund['returns_1yr'], color='red', linestyle='--', label='Best Fund')
    plt.title('Comparison of Selected Fund(s) with Other Funds')
    plt.xlabel('Fund Name')
    plt.ylabel('1-Year Returns')
    plt.xticks(rotation=45)
    plt.legend()

    # Save plot to a string buffer
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    return comparison, plot_url

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        fund_names = [name.strip() for name in request.form['fund_names'].split(',')]
        comparison, plot_url = compare_funds(fund_names)

        if comparison is None:
            return render_template('index.html', error=plot_url)  # plot_url holds the error message here
        
        return render_template('index.html', tables=[comparison.to_html(classes='data')], plot_url=plot_url)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
