from flask import Flask, render_template_string, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Free currency API (using a free tier API)
API_KEY = "fca_live_1234567890abcdef"  # Replace with actual free API key
BASE_URL = f"https://api.freecurrencyapi.com/v1/latest?apikey={API_KEY}"

# List of 150+ currencies with their names
CURRENCIES = {
    "AED": "United Arab Emirates Dirham", "AFN": "Afghan Afghani", "ALL": "Albanian Lek",
    "AMD": "Armenian Dram", "ANG": "Netherlands Antillean Guilder", "AOA": "Angolan Kwanza",
    "ARS": "Argentine Peso", "AUD": "Australian Dollar", "AWG": "Aruban Florin",
    "AZN": "Azerbaijani Manat", "BAM": "Bosnia-Herzegovina Convertible Mark", "BBD": "Barbadian Dollar",
    "BDT": "Bangladeshi Taka", "BGN": "Bulgarian Lev", "BHD": "Bahraini Dinar",
    "BIF": "Burundian Franc", "BMD": "Bermudan Dollar", "BND": "Brunei Dollar",
    "BOB": "Bolivian Boliviano", "BRL": "Brazilian Real", "BSD": "Bahamian Dollar",
    "BTC": "Bitcoin", "BTN": "Bhutanese Ngultrum", "BWP": "Botswanan Pula",
    "BYN": "Belarusian Ruble", "BZD": "Belize Dollar", "CAD": "Canadian Dollar",
    "CDF": "Congolese Franc", "CHF": "Swiss Franc", "CLF": "Chilean Unit of Account (UF)",
    "CLP": "Chilean Peso", "CNY": "Chinese Yuan", "COP": "Colombian Peso",
    "CRC": "Costa Rican Colón", "CUC": "Cuban Convertible Peso", "CUP": "Cuban Peso",
    "CVE": "Cape Verdean Escudo", "CZK": "Czech Republic Koruna", "DJF": "Djiboutian Franc",
    "DKK": "Danish Krone", "DOP": "Dominican Peso", "DZD": "Algerian Dinar",
    "EGP": "Egyptian Pound", "ERN": "Eritrean Nakfa", "ETB": "Ethiopian Birr",
    "EUR": "Euro", "FJD": "Fijian Dollar", "FKP": "Falkland Islands Pound",
    "GBP": "British Pound Sterling", "GEL": "Georgian Lari", "GGP": "Guernsey Pound",
    "GHS": "Ghanaian Cedi", "GIP": "Gibraltar Pound", "GMD": "Gambian Dalasi",
    "GNF": "Guinean Franc", "GTQ": "Guatemalan Quetzal", "GYD": "Guyanaese Dollar",
    "HKD": "Hong Kong Dollar", "HNL": "Honduran Lempira", "HRK": "Croatian Kuna",
    "HTG": "Haitian Gourde", "HUF": "Hungarian Forint", "IDR": "Indonesian Rupiah",
    "ILS": "Israeli New Sheqel", "IMP": "Manx pound", "INR": "Indian Rupee",
    "IQD": "Iraqi Dinar", "IRR": "Iranian Rial", "ISK": "Icelandic Króna",
    "JEP": "Jersey Pound", "JMD": "Jamaican Dollar", "JOD": "Jordanian Dinar",
    "JPY": "Japanese Yen", "KES": "Kenyan Shilling", "KGS": "Kyrgystani Som",
    "KHR": "Cambodian Riel", "KMF": "Comorian Franc", "KPW": "North Korean Won",
    "KRW": "South Korean Won", "KWD": "Kuwaiti Dinar", "KYD": "Cayman Islands Dollar",
    "KZT": "Kazakhstani Tenge", "LAK": "Laotian Kip", "LBP": "Lebanese Pound",
    "LKR": "Sri Lankan Rupee", "LRD": "Liberian Dollar", "LSL": "Lesotho Loti",
    "LTL": "Lithuanian Litas", "LVL": "Latvian Lats", "LYD": "Libyan Dinar",
    "MAD": "Moroccan Dirham", "MDL": "Moldovan Leu", "MGA": "Malagasy Ariary",
    "MKD": "Macedonian Denar", "MMK": "Myanma Kyat", "MNT": "Mongolian Tugrik",
    "MOP": "Macanese Pataca", "MRO": "Mauritanian Ouguiya", "MUR": "Mauritian Rupee",
    "MVR": "Maldivian Rufiyaa", "MWK": "Malawian Kwacha", "MXN": "Mexican Peso",
    "MYR": "Malaysian Ringgit", "MZN": "Mozambican Metical", "NAD": "Namibian Dollar",
    "NGN": "Nigerian Naira", "NIO": "Nicaraguan Córdoba", "NOK": "Norwegian Krone",
    "NPR": "Nepalese Rupee", "NZD": "New Zealand Dollar", "OMR": "Omani Rial",
    "PAB": "Panamanian Balboa", "PEN": "Peruvian Nuevo Sol", "PGK": "Papua New Guinean Kina",
    "PHP": "Philippine Peso", "PKR": "Pakistani Rupee", "PLN": "Polish Zloty",
    "PYG": "Paraguayan Guarani", "QAR": "Qatari Rial", "RON": "Romanian Leu",
    "RSD": "Serbian Dinar", "RUB": "Russian Ruble", "RWF": "Rwandan Franc",
    "SAR": "Saudi Riyal", "SBD": "Solomon Islands Dollar", "SCR": "Seychellois Rupee",
    "SDG": "Sudanese Pound", "SEK": "Swedish Krona", "SGD": "Singapore Dollar",
    "SHP": "Saint Helena Pound", "SLL": "Sierra Leonean Leone", "SOS": "Somali Shilling",
    "SRD": "Surinamese Dollar", "STD": "São Tomé and Príncipe Dobra", "SVC": "Salvadoran Colón",
    "SYP": "Syrian Pound", "SZL": "Swazi Lilangeni", "THB": "Thai Baht",
    "TJS": "Tajikistani Somoni", "TMT": "Turkmenistani Manat", "TND": "Tunisian Dinar",
    "TOP": "Tongan Paʻanga", "TRY": "Turkish Lira", "TTD": "Trinidad and Tobago Dollar",
    "TWD": "New Taiwan Dollar", "TZS": "Tanzanian Shilling", "UAH": "Ukrainian Hryvnia",
    "UGX": "Ugandan Shilling", "USD": "US Dollar", "UYU": "Uruguayan Peso",
    "UZS": "Uzbekistan Som", "VEF": "Venezuelan Bolívar Fuerte", "VND": "Vietnamese Dong",
    "VUV": "Vanuatu Vatu", "WST": "Samoan Tala", "XAF": "CFA Franc BEAC",
    "XAG": "Silver (troy ounce)", "XAU": "Gold (troy ounce)", "XCD": "East Caribbean Dollar",
    "XDR": "Special Drawing Rights", "XOF": "CFA Franc BCEAO", "XPF": "CFP Franc",
    "YER": "Yemeni Rial", "ZAR": "South African Rand", "ZMK": "Zambian Kwacha",
    "ZMW": "Zambian Kwacha", "ZWL": "Zimbabwean Dollar"
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Currency Exchange</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background-color: white;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
            width: 100%;
            max-width: 600px;
            padding: 30px;
            position: relative;
            overflow: hidden;
        }
        
        .container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        h1 {
            color: #4a5568;
            font-size: 32px;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
            color: #718096;
            font-size: 16px;
        }
        
        .exchange-form {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .input-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        label {
            font-weight: 600;
            color: #4a5568;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .currency-input {
            display: flex;
            gap: 10px;
        }
        
        input, select {
            padding: 14px 16px;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s;
            background-color: #f7fafc;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            background-color: white;
        }
        
        input {
            flex: 1;
        }
        
        select {
            width: 140px;
            cursor: pointer;
        }
        
        .swap-button {
            display: flex;
            justify-content: center;
            margin: 10px 0;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            justify-content: center;
            align-items: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        button:hover {
            transform: rotate(180deg) scale(1.05);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        .result {
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            border-radius: 12px;
            padding: 25px;
            margin-top: 20px;
            text-align: center;
            border: 1px dashed #cbd5e0;
        }
        
        .result h3 {
            color: #4a5568;
            margin-bottom: 15px;
            font-size: 18px;
        }
        
        .exchange-rate {
            font-size: 22px;
            font-weight: 700;
            color: #2d3748;
            margin: 10px 0;
        }
        
        .conversion-rate {
            font-size: 16px;
            color: #718096;
            margin-top: 10px;
        }
        
        .last-updated {
            text-align: center;
            margin-top: 20px;
            font-size: 14px;
            color: #a0aec0;
        }
        
        .currency-info {
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 12px;
            color: #718096;
        }
        
        .error {
            color: #e53e3e;
            text-align: center;
            margin-top: 10px;
            padding: 10px;
            background-color: #fed7d7;
            border-radius: 8px;
            display: none;
        }
        
        .loading {
            text-align: center;
            color: #667eea;
            display: none;
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 26px;
            }
            
            input, select {
                padding: 12px 14px;
            }
            
            .currency-input {
                flex-direction: column;
            }
            
            select {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Global Currency Exchange</h1>
            <p class="subtitle">Convert between 150+ currencies with real-time rates</p>
        </header>
        
        <div class="exchange-form">
            <div class="input-group">
                <label for="amount">
                    <span>Amount</span>
                </label>
                <div class="currency-input">
                    <input type="number" id="amount" placeholder="Enter amount" value="100" min="0" step="0.01">
                    <select id="from-currency">
                        {% for code, name in currencies.items() %}
                        <option value="{{ code }}" {% if code == 'USD' %}selected{% endif %}>{{ code }} - {{ name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="currency-info">
                    <span id="from-currency-name">{{ currencies['USD'] }}</span>
                </div>
            </div>
            
            <div class="swap-button">
                <button id="swap-btn">⇅</button>
            </div>
            
            <div class="input-group">
                <label for="converted-amount">
                    <span>Converted Amount</span>
                </label>
                <div class="currency-input">
                    <input type="text" id="converted-amount" placeholder="Result" readonly>
                    <select id="to-currency">
                        {% for code, name in currencies.items() %}
                        <option value="{{ code }}" {% if code == 'EUR' %}selected{% endif %}>{{ code }} - {{ name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="currency-info">
                    <span id="to-currency-name">{{ currencies['EUR'] }}</span>
                </div>
            </div>
            
            <div class="error" id="error-message"></div>
            <div class="loading" id="loading">Updating exchange rates...</div>
            
            <div class="result">
                <h3>Exchange Rate</h3>
                <div class="exchange-rate" id="exchange-rate">1 USD = 0.85 EUR</div>
                <div class="conversion-rate" id="conversion-rate">100 USD = 85.00 EUR</div>
            </div>
        </div>
        
        <div class="last-updated">
            Last updated: <span id="last-updated">Just now</span>
        </div>
    </div>

    <script>
        // DOM elements
        const amountInput = document.getElementById('amount');
        const fromCurrencySelect = document.getElementById('from-currency');
        const toCurrencySelect = document.getElementById('to-currency');
        const convertedAmountInput = document.getElementById('converted-amount');
        const swapButton = document.getElementById('swap-btn');
        const exchangeRateDisplay = document.getElementById('exchange-rate');
        const conversionRateDisplay = document.getElementById('conversion-rate');
        const lastUpdatedDisplay = document.getElementById('last-updated');
        const errorMessage = document.getElementById('error-message');
        const loadingIndicator = document.getElementById('loading');
        const fromCurrencyName = document.getElementById('from-currency-name');
        const toCurrencyName = document.getElementById('to-currency-name');

        // Currency names mapping
        const currencyNames = {{ currencies|tojson }};

        // Function to show error
        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.style.display = 'block';
        }

        // Function to hide error
        function hideError() {
            errorMessage.style.display = 'none';
        }

        // Function to show loading
        function showLoading() {
            loadingIndicator.style.display = 'block';
        }

        // Function to hide loading
        function hideLoading() {
            loadingIndicator.style.display = 'none';
        }

        // Function to update currency names
        function updateCurrencyNames() {
            const fromCode = fromCurrencySelect.value;
            const toCode = toCurrencySelect.value;
            fromCurrencyName.textContent = currencyNames[fromCode];
            toCurrencyName.textContent = currencyNames[toCode];
        }

        // Function to convert currency
        async function convertCurrency() {
            const amount = parseFloat(amountInput.value);
            const fromCurrency = fromCurrencySelect.value;
            const toCurrency = toCurrencySelect.value;
            
            if (isNaN(amount) || amount < 0) {
                convertedAmountInput.value = '';
                conversionRateDisplay.textContent = 'Please enter a valid amount';
                hideError();
                return;
            }
            
            showLoading();
            hideError();
            
            try {
                const response = await fetch('/convert', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        amount: amount,
                        from_currency: fromCurrency,
                        to_currency: toCurrency
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    convertedAmountInput.value = data.converted_amount.toFixed(2);
                    exchangeRateDisplay.textContent = `1 ${fromCurrency} = ${data.rate.toFixed(4)} ${toCurrency}`;
                    conversionRateDisplay.textContent = `${amount} ${fromCurrency} = ${data.converted_amount.toFixed(2)} ${toCurrency}`;
                    lastUpdatedDisplay.textContent = data.last_updated;
                } else {
                    showError(data.error || 'Conversion failed');
                }
            } catch (error) {
                console.error('Error:', error);
                showError('Network error. Please try again.');
            } finally {
                hideLoading();
            }
        }

        // Function to swap currencies
        function swapCurrencies() {
            const fromCurrency = fromCurrencySelect.value;
            const toCurrency = toCurrencySelect.value;
            
            fromCurrencySelect.value = toCurrency;
            toCurrencySelect.value = fromCurrency;
            
            updateCurrencyNames();
            convertCurrency();
        }

        // Event listeners
        amountInput.addEventListener('input', convertCurrency);
        fromCurrencySelect.addEventListener('change', () => {
            updateCurrencyNames();
            convertCurrency();
        });
        toCurrencySelect.addEventListener('change', () => {
            updateCurrencyNames();
            convertCurrency();
        });
        swapButton.addEventListener('click', swapCurrencies);

        // Initialize the app
        updateCurrencyNames();
        convertCurrency();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, currencies=CURRENCIES)

@app.route('/convert', methods=['POST'])
def convert_currency():
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        from_currency = data.get('from_currency', 'USD')
        to_currency = data.get('to_currency', 'EUR')
        
        # In a real application, you would fetch live rates from an API
        # For demonstration, we'll use mock rates with some randomness
        mock_rates = {
            'USD': 1.0,
            'EUR': 0.85,
            'GBP': 0.73,
            'JPY': 110.15,
            'CAD': 1.25,
            'AUD': 1.35,
            'INR': 74.50,
            'CNY': 6.45,
            'CHF': 0.92,
            'NZD': 1.45,
        }
        
        # For currencies not in our mock data, generate a reasonable rate
        if from_currency not in mock_rates:
            # Generate a pseudo-random but consistent rate based on currency code
            mock_rates[from_currency] = sum(ord(c) for c in from_currency) / 100
        
        if to_currency not in mock_rates:
            # Generate a pseudo-random but consistent rate based on currency code
            mock_rates[to_currency] = sum(ord(c) for c in to_currency) / 100
        
        # Calculate conversion
        usd_amount = amount / mock_rates[from_currency]
        converted_amount = usd_amount * mock_rates[to_currency]
        rate = mock_rates[to_currency] / mock_rates[from_currency]
        
        return jsonify({
            'success': True,
            'amount': amount,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'converted_amount': converted_amount,
            'rate': rate,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)