// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// State management
let token = localStorage.getItem('token');
let userId = localStorage.getItem('userId');
let username = localStorage.getItem('username');

// Helper Functions
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

function showMessage(elementId, message, type) {
    const messageElement = document.getElementById(elementId);
    if (messageElement) {
        messageElement.textContent = message;
        messageElement.className = `message ${type}`;
        messageElement.style.display = 'block';
        
        // Hide message after 5 seconds
        setTimeout(() => {
            messageElement.style.display = 'none';
        }, 5000);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatCurrency(amount) {
    return `$${parseFloat(amount).toFixed(2)}`;
}

// API Functions
async function apiRequest(endpoint, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const options = {
        method,
        headers
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Request failed');
        }
        
        return result;
    } catch (error) {
        throw error;
    }
}

// Authentication Functions
async function login(username, password) {
    try {
        const result = await apiRequest('/api/login', 'POST', { username, password });
        
        // Store credentials
        token = result.token;
        userId = result.user_id;
        localStorage.setItem('token', token);
        localStorage.setItem('userId', userId);
        localStorage.setItem('username', result.username);
        
        return result;
    } catch (error) {
        throw error;
    }
}

async function register(userData) {
    try {
        const result = await apiRequest('/api/register', 'POST', userData);
        
        // Store credentials
        token = result.token;
        userId = result.user_id;
        localStorage.setItem('token', token);
        localStorage.setItem('userId', userId);
        localStorage.setItem('username', userData.username);
        
        return result;
    } catch (error) {
        throw error;
    }
}

function logout() {
    token = null;
    userId = null;
    username = null;
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    
    // Hide dashboard and show login
    document.getElementById('dashboard').style.display = 'none';
    document.querySelector('.login-container').style.display = 'block';
}

// Dashboard Functions
async function loadAccounts() {
    try {
        const result = await apiRequest('/api/accounts');
        const accounts = result.accounts;
        
        // Update accounts list
        const accountsList = document.getElementById('accounts-list');
        accountsList.innerHTML = '';
        
        accounts.forEach(account => {
            const accountCard = document.createElement('div');
            accountCard.className = 'account-card';
            accountCard.innerHTML = `
                <div class="account-info">
                    <div class="account-number">Account: ${account.account_number}</div>
                    <div class="account-type">Type: ${account.account_type}</div>
                </div>
                <div class="account-balance">${formatCurrency(account.balance)}</div>
            `;
            accountsList.appendChild(accountCard);
        });
        
        // Update account dropdowns
        const accountNumbers = accounts.map(acc => acc.account_number);
        updateAccountDropdowns(accountNumbers);
        
        // Load transactions for first account
        if (accounts.length > 0) {
            loadTransactions(accounts[0].account_number);
        }
        
        return accounts;
    } catch (error) {
        console.error('Failed to load accounts:', error);
        throw error;
    }
}

function updateAccountDropdowns(accountNumbers) {
    const dropdowns = ['deposit-account', 'withdraw-account', 'transfer-from'];
    
    dropdowns.forEach(dropdownId => {
        const dropdown = document.getElementById(dropdownId);
        if (dropdown) {
            dropdown.innerHTML = '<option value="">Select Account</option>';
            accountNumbers.forEach(accNum => {
                const option = document.createElement('option');
                option.value = accNum;
                option.textContent = accNum;
                dropdown.appendChild(option);
            });
        }
    });
}

async function loadTransactions(accountNumber) {
    try {
        const result = await apiRequest(`/api/transactions/${accountNumber}`);
        const transactions = result.transactions;
        
        const transactionsList = document.getElementById('transactions-list');
        transactionsList.innerHTML = '';
        
        if (transactions.length === 0) {
            transactionsList.innerHTML = '<p style="padding: 2rem; text-align: center;">No transactions yet</p>';
            return;
        }
        
        // Sort by timestamp (newest first)
        transactions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        // Show only last 10 transactions
        transactions.slice(0, 10).forEach(trans => {
            const transItem = document.createElement('div');
            transItem.className = 'transaction-item';
            
            const isCredit = trans.to_account === accountNumber;
            const amountClass = isCredit ? 'credit' : 'debit';
            const amountPrefix = isCredit ? '+' : '-';
            
            transItem.innerHTML = `
                <div class="transaction-date">${formatDate(trans.timestamp)}</div>
                <div class="transaction-description">${trans.description}</div>
                <div class="transaction-amount ${amountClass}">${amountPrefix}${formatCurrency(trans.amount)}</div>
                <div class="transaction-type">${trans.type}</div>
            `;
            transactionsList.appendChild(transItem);
        });
    } catch (error) {
        console.error('Failed to load transactions:', error);
    }
}

async function deposit(accountNumber, amount) {
    try {
        const result = await apiRequest('/api/deposit', 'POST', {
            account_number: accountNumber,
            amount: parseFloat(amount)
        });
        return result;
    } catch (error) {
        throw error;
    }
}

async function withdraw(accountNumber, amount) {
    try {
        const result = await apiRequest('/api/withdraw', 'POST', {
            account_number: accountNumber,
            amount: parseFloat(amount)
        });
        return result;
    } catch (error) {
        throw error;
    }
}

async function transfer(fromAccount, toAccount, amount, description) {
    try {
        const result = await apiRequest('/api/transfer', 'POST', {
            from_account: fromAccount,
            to_account: toAccount,
            amount: parseFloat(amount),
            description: description || 'Transfer'
        });
        return result;
    } catch (error) {
        throw error;
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Check if already logged in
    if (token && document.getElementById('dashboard')) {
        showDashboard();
    }
    
    // Login Form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            try {
                await login(username, password);
                showMessage('login-message', 'Login successful!', 'success');
                setTimeout(() => showDashboard(), 1000);
            } catch (error) {
                showMessage('login-message', error.message, 'error');
            }
        });
    }
    
    // Register Form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('register-username').value;
            const email = document.getElementById('register-email').value;
            const fullName = document.getElementById('register-fullname').value;
            const password = document.getElementById('register-password').value;
            const confirmPassword = document.getElementById('register-confirm-password').value;
            
            if (password !== confirmPassword) {
                showMessage('register-message', 'Passwords do not match!', 'error');
                return;
            }
            
            try {
                await register({
                    username,
                    email,
                    full_name: fullName,
                    password
                });
                showMessage('register-message', 'Registration successful!', 'success');
                setTimeout(() => showDashboard(), 1000);
            } catch (error) {
                showMessage('register-message', error.message, 'error');
            }
        });
    }
    
    // Deposit Form
    const depositForm = document.getElementById('depositForm');
    if (depositForm) {
        depositForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const accountNumber = document.getElementById('deposit-account').value;
            const amount = e.target.elements.amount.value;
            
            try {
                const result = await deposit(accountNumber, amount);
                showMessage('deposit-message', `Deposited ${formatCurrency(amount)}! New balance: ${formatCurrency(result.new_balance)}`, 'success');
                await loadAccounts();
                e.target.reset();
            } catch (error) {
                showMessage('deposit-message', error.message, 'error');
            }
        });
    }
    
    // Withdraw Form
    const withdrawForm = document.getElementById('withdrawForm');
    if (withdrawForm) {
        withdrawForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const accountNumber = document.getElementById('withdraw-account').value;
            const amount = e.target.elements.amount.value;
            
            try {
                const result = await withdraw(accountNumber, amount);
                showMessage('withdraw-message', `Withdrew ${formatCurrency(amount)}! New balance: ${formatCurrency(result.new_balance)}`, 'success');
                await loadAccounts();
                e.target.reset();
            } catch (error) {
                showMessage('withdraw-message', error.message, 'error');
            }
        });
    }
    
    // Transfer Form
    const transferForm = document.getElementById('transferForm');
    if (transferForm) {
        transferForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fromAccount = document.getElementById('transfer-from').value;
            const toAccount = e.target.elements.to_account.value;
            const amount = e.target.elements.amount.value;
            const description = e.target.elements.description.value;
            
            try {
                const result = await transfer(fromAccount, toAccount, amount, description);
                showMessage('transfer-message', `Transferred ${formatCurrency(amount)}! New balance: ${formatCurrency(result.new_balance)}`, 'success');
                await loadAccounts();
                e.target.reset();
            } catch (error) {
                showMessage('transfer-message', error.message, 'error');
            }
        });
    }
});

async function showDashboard() {
    const username = localStorage.getItem('username');
    
    // Hide login container
    const loginContainer = document.querySelector('.login-container');
    if (loginContainer) {
        loginContainer.style.display = 'none';
    }
    
    // Show dashboard
    const dashboard = document.getElementById('dashboard');
    if (dashboard) {
        dashboard.style.display = 'block';
        
        // Update username
        const userNameElement = document.getElementById('user-name');
        if (userNameElement) {
            userNameElement.textContent = username;
        }
        
        // Load accounts and transactions
        await loadAccounts();
    }
}

// Make functions globally accessible
window.showTab = showTab;
window.logout = logout;