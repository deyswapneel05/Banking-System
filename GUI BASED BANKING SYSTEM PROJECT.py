import argparse
import csv
import hashlib
import os
import random
import sys
from datetime import datetime
import tempfile
import unittest

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False

ACCOUNTS_FILE = 'accounts.txt'
TRANSACTIONS_FILE = 'transactions.txt'
ADMIN_PASSWORD = 'admin123'

def _write_csv_atomic(path, fieldnames, rows):
    tmp = path + '.tmp'
    with open(tmp, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    os.replace(tmp, path)

def ensure_files(accounts_file=ACCOUNTS_FILE, transactions_file=TRANSACTIONS_FILE):
    if not os.path.exists(accounts_file) or os.path.getsize(accounts_file) == 0:
        with open(accounts_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['AccountNumber', 'Name', 'PasswordHash', 'Balance'])
            writer.writeheader()
    if not os.path.exists(transactions_file) or os.path.getsize(transactions_file) == 0:
        with open(transactions_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['AccountNumber', 'Type', 'Amount', 'DateTime'])
            writer.writeheader()

def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode('utf-8')).hexdigest()

def generate_account_number(existing: dict) -> str:
    while True:
        num = str(random.randint(100000, 999999))
        if num not in existing:
            return num

def load_accounts(accounts_file=ACCOUNTS_FILE) -> dict:
    accounts = {}
    if not os.path.exists(accounts_file):
        return accounts
    with open(accounts_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get('AccountNumber'):
                continue
            acc = row['AccountNumber']
            try:
                bal = float(row.get('Balance') or 0.0)
            except Exception:
                bal = 0.0
            accounts[acc] = {'name': row.get('Name', ''), 'password': row.get('PasswordHash', ''), 'balance': bal}
    return accounts

def save_accounts(accounts: dict, accounts_file=ACCOUNTS_FILE):
    rows = []
    for acc, info in accounts.items():
        rows.append({'AccountNumber': acc, 'Name': info.get('name', ''), 'PasswordHash': info.get('password', ''), 'Balance': f"{info.get('balance', 0.0):.2f}"})
    _write_csv_atomic(accounts_file, ['AccountNumber', 'Name', 'PasswordHash', 'Balance'], rows)

def _ensure_transactions_file(transactions_file):
    if not os.path.exists(transactions_file) or os.path.getsize(transactions_file) == 0:
        with open(transactions_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['AccountNumber', 'Type', 'Amount', 'DateTime'])
            writer.writeheader()

def log_transaction(account_number: str, tx_type: str, amount: float, transactions_file=TRANSACTIONS_FILE):
    _ensure_transactions_file(transactions_file)
    with open(transactions_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['AccountNumber', 'Type', 'Amount', 'DateTime'])
        writer.writerow({'AccountNumber': account_number, 'Type': tx_type, 'Amount': f"{amount:.2f}", 'DateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

def get_transactions_for_account(account_number: str, transactions_file=TRANSACTIONS_FILE) -> list:
    txs = []
    if not os.path.exists(transactions_file):
        return txs
    with open(transactions_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('AccountNumber') == account_number:
                txs.append(row)
    return txs

def change_password(accounts: dict, account_number: str, new_password: str, accounts_file=ACCOUNTS_FILE):
    if account_number not in accounts:
        raise KeyError('Account not found')
    accounts[account_number]['password'] = hash_password(new_password)
    save_accounts(accounts, accounts_file)

def delete_account(accounts: dict, account_number: str, accounts_file=ACCOUNTS_FILE):
    if account_number in accounts:
        del accounts[account_number]
        save_accounts(accounts, accounts_file)
        return True
    return False

def reset_password(accounts: dict, account_number: str, accounts_file=ACCOUNTS_FILE) -> str:
    if account_number not in accounts:
        raise KeyError('Account not found')
    temp = f"TEMP{random.randint(1000,9999)}"
    accounts[account_number]['password'] = hash_password(temp + '_TEMP')
    save_accounts(accounts, accounts_file)
    return temp

def is_temp_password(stored_hash: str, raw_password: str) -> bool:
    return stored_hash == hash_password(raw_password + '_TEMP')

class BankingCLI:
    def __init__(self, accounts_file=ACCOUNTS_FILE, transactions_file=TRANSACTIONS_FILE):
        ensure_files(accounts_file, transactions_file)
        self.accounts_file = accounts_file
        self.transactions_file = transactions_file
        self.accounts = load_accounts(self.accounts_file)
        self.current_account = None

    def main_menu(self):
        try:
            while True:
                print('\n=== Banking System ===')
                print('1. Create Account')
                print('2. Login')
                print('3. Forget Password')
                print('4. Admin Panel')
                print('5. Exit')
                choice = input('Enter choice: ').strip()
                if choice == '1':
                    self.create_account_cli()
                elif choice == '2':
                    self.login_cli()
                elif choice == '3':
                    self.forget_password_cli()
                elif choice == '4':
                    self.admin_panel_cli()
                elif choice == '5':
                    print('Goodbye!')
                    break
                else:
                    print('Invalid choice')
        except (KeyboardInterrupt, EOFError):
            print('\nExiting...')

    def create_account_cli(self):
        name = input('Enter your name: ').strip()
        if not name:
            print('Name required')
            return
        try:
            initial_deposit = float(input('Enter initial deposit: ').strip())
            if initial_deposit < 0:
                raise ValueError()
        except Exception:
            print('Invalid deposit')
            return
        password = input('Enter password (min 4 chars): ')
        if not password or len(password) < 4:
            print('Password too short')
            return
        acc_number = generate_account_number(self.accounts)
        self.accounts[acc_number] = {'name': name, 'password': hash_password(password), 'balance': initial_deposit}
        save_accounts(self.accounts, self.accounts_file)
        if initial_deposit > 0:
            log_transaction(acc_number, 'Deposit', initial_deposit, self.transactions_file)
        print(f'Account created successfully! Account Number: {acc_number}')

    def login_cli(self):
        acc = input('Enter account number: ').strip()
        pw = input('Enter password: ')
        if acc not in self.accounts:
            print('Account not found')
            return
        stored = self.accounts[acc]['password']
        if stored == hash_password(pw):
            self.current_account = acc
            print('Login successful')
            self.user_menu()
        elif is_temp_password(stored, pw):
            print('Logged in with temporary password — you must set a new password now.')
            while True:
                new_pw = input('Enter new password: ').strip()
                if not new_pw or len(new_pw) < 4:
                    print('Password too short')
                    continue
                confirm = input('Confirm new password: ').strip()
                if new_pw != confirm:
                    print('Passwords do not match')
                    continue
                change_password(self.accounts, acc, new_pw, self.accounts_file)
                break
            self.current_account = acc
            self.user_menu()
        else:
            print('Invalid credentials')

    def forget_password_cli(self):
        acc = input('Enter your account number: ').strip()
        if acc not in self.accounts:
            print('Account not found')
            return
        temp = reset_password(self.accounts, acc, self.accounts_file)
        print(f'Your temporary password is: {temp} — use it to login and immediately change your password.')

    def user_menu(self):
        try:
            while self.current_account:
                bal = self.accounts[self.current_account]['balance']
                print(f'\nAccount: {self.current_account} | Balance: {bal:.2f}')
                print('1. Deposit')
                print('2. Withdraw')
                print('3. Transfer')
                print('4. Change Password')
                print('5. Transactions')
                print('6. Logout')
                choice = input('Enter choice: ').strip()
                if choice == '1':
                    self.deposit()
                elif choice == '2':
                    self.withdraw()
                elif choice == '3':
                    self.transfer()
                elif choice == '4':
                    self.change_password_cli()
                elif choice == '5':
                    self.show_history()
                elif choice == '6':
                    self.current_account = None
                else:
                    print('Invalid choice')
        except (KeyboardInterrupt, EOFError):
            print('\nLogging out...')
            self.current_account = None

    def deposit(self):
        try:
            amt = float(input('Enter amount to deposit: ').strip())
            if amt <= 0:
                raise ValueError()
        except Exception:
            print('Invalid amount')
            return
        acc = self.current_account
        self.accounts[acc]['balance'] += amt
        save_accounts(self.accounts, self.accounts_file)
        log_transaction(acc, 'Deposit', amt, self.transactions_file)
        print(f"Deposit successful, new balance: {self.accounts[acc]['balance']:.2f}")

    def withdraw(self):
        try:
            amt = float(input('Enter amount to withdraw: ').strip())
            if amt <= 0:
                raise ValueError()
        except Exception:
            print('Invalid amount')
            return
        acc = self.current_account
        if self.accounts[acc]['balance'] < amt:
            print('Insufficient balance')
            return
        self.accounts[acc]['balance'] -= amt
        save_accounts(self.accounts, self.accounts_file)
        log_transaction(acc, 'Withdrawal', amt, self.transactions_file)
        print(f"Withdrawal successful, new balance: {self.accounts[acc]['balance']:.2f}")

    def transfer(self):
        to_acc = input('Recipient account number: ').strip()
        if to_acc not in self.accounts:
            print('Recipient not found')
            return
        try:
            amt = float(input('Enter amount to transfer: ').strip())
            if amt <= 0:
                raise ValueError()
        except Exception:
            print('Invalid amount')
            return
        if self.accounts[self.current_account]['balance'] < amt:
            print('Insufficient funds')
            return
        self.accounts[self.current_account]['balance'] -= amt
        self.accounts[to_acc]['balance'] += amt
        save_accounts(self.accounts, self.accounts_file)
        log_transaction(self.current_account, 'Transfer Out', amt, self.transactions_file)
        log_transaction(to_acc, 'Transfer In', amt, self.transactions_file)
        print('Transfer complete')

    def change_password_cli(self):
        old_pw = input('Enter current password: ').strip()
        if self.accounts[self.current_account]['password'] != hash_password(old_pw):
            print('Incorrect current password')
            return
        new_pw = input('Enter new password: ').strip()
        if not new_pw or len(new_pw) < 4:
            print('Password too short')
            return
        change_password(self.accounts, self.current_account, new_pw, self.accounts_file)
        print('Password changed')

    def show_history(self):
        txs = get_transactions_for_account(self.current_account, self.transactions_file)
        if not txs:
            print('No transactions')
            return
        print('\nTransactions:')
        for t in txs:
            print(f"{t.get('Type','')}\t{t.get('Amount','')}\t{t.get('DateTime','')}")

    def admin_panel_cli(self):
        pw = input('Enter admin password: ').strip()
        if pw != ADMIN_PASSWORD:
            print('Access denied')
            return
        print('\n--- Admin Panel ---')
        for acc, data in self.accounts.items():
            print(f"{acc}: {data['name']} | Balance: {data['balance']:.2f}")
        action = input('(R)eset password / (D)elete account / Enter to exit: ').strip().lower()
        if action == 'r':
            acc = input('Account number to reset: ').strip()
            if acc in self.accounts:
                temp = reset_password(self.accounts, acc, self.accounts_file)
                print(f'Temporary password for {acc}: {temp}')
        elif action == 'd':
            acc = input('Account number to delete: ').strip()
            confirm = input(f'Are you sure you want to delete {acc}? (yes/no): ').strip().lower()
            if confirm == 'yes':
                delete_account(self.accounts, acc, self.accounts_file)
                print(f'Account {acc} deleted')

if TK_AVAILABLE:
    class BankingGUI:
        COLOR_BG = '#f4f7fb'
        COLOR_HEADER = '#2b6cb0'
        COLOR_PRIMARY = '#4299e1'
        COLOR_ACCENT = '#48bb78'
        COLOR_WARN = '#f6ad55'

        def __init__(self, root, accounts_file=ACCOUNTS_FILE, transactions_file=TRANSACTIONS_FILE):
            self.root = root
            self.root.title('Banking System')
            self.root.geometry('540x480')
            self.root.configure(bg=self.COLOR_BG)
            self.accounts_file = accounts_file
            self.transactions_file = transactions_file
            ensure_files(self.accounts_file, self.transactions_file)
            self.accounts = load_accounts(self.accounts_file)
            self.current_account = None
            self.build_main_menu()

        def styled_button(self, parent, text, command, bg=None):
            btn = tk.Button(parent, text=text, command=command, bg=bg or self.COLOR_PRIMARY, fg='white', bd=0, padx=8, pady=6, font=('Helvetica', 11, 'bold'))
            return btn

        def clear(self):
            for w in self.root.winfo_children():
                w.destroy()

        def build_main_menu(self):
            self.clear()
            header = tk.Frame(self.root, bg=self.COLOR_HEADER)
            header.pack(fill='x')
            tk.Label(header, text='Banking System', bg=self.COLOR_HEADER, fg='white', font=('Helvetica', 18, 'bold')).pack(pady=12)

            body = tk.Frame(self.root, bg=self.COLOR_BG, padx=16, pady=16)
            body.pack(fill='both', expand=True)

            self.styled_button(body, 'Create Account', self.create_account, bg=self.COLOR_ACCENT).pack(fill='x', pady=6)
            self.styled_button(body, 'Login', self.login, bg=self.COLOR_PRIMARY).pack(fill='x', pady=6)
            self.styled_button(body, 'Forget Password', self.forget_password, bg=self.COLOR_WARN).pack(fill='x', pady=6)
            self.styled_button(body, 'Admin Panel', self.open_admin_panel, bg='#ed64a6').pack(fill='x', pady=6)
            tk.Label(body, text='(Use CLI with --cli if GUI not available)', bg=self.COLOR_BG, fg='#4a5568', font=('Helvetica', 9)).pack(pady=10)

        def create_account(self):
            name = simpledialog.askstring('Create Account', 'Enter your name:', parent=self.root)
            if not name:
                return
            deposit = simpledialog.askstring('Create Account', 'Enter initial deposit:', parent=self.root)
            try:
                deposit_val = float(deposit or '0')
                if deposit_val < 0:
                    raise ValueError()
            except Exception:
                messagebox.showerror('Error', 'Invalid deposit amount')
                return
            pw = simpledialog.askstring('Create Account', 'Enter password (min 4 chars):', show='*', parent=self.root)
            if not pw or len(pw) < 4:
                messagebox.showerror('Error', 'Password too short')
                return
            acc = generate_account_number(self.accounts)
            self.accounts[acc] = {'name': name, 'password': hash_password(pw), 'balance': deposit_val}
            save_accounts(self.accounts, self.accounts_file)
            if deposit_val > 0:
                log_transaction(acc, 'Deposit', deposit_val, self.transactions_file)
            messagebox.showinfo('Success', f'Account created! Account number: {acc}')

        def login(self):
            acc = simpledialog.askstring('Login', 'Enter account number:', parent=self.root)
            pw = simpledialog.askstring('Login', 'Enter password:', show='*', parent=self.root)
            if not acc or not pw:
                return
            if acc not in self.accounts:
                messagebox.showerror('Error', 'Account not found')
                return
            stored_hash = self.accounts[acc]['password']
            if stored_hash == hash_password(pw):
                self.current_account = acc
                messagebox.showinfo('Welcome', f'Welcome, {self.accounts[acc]["name"]}!')
                self.open_dashboard()
            elif is_temp_password(stored_hash, pw):
                messagebox.showinfo('Change Password', 'You are using a temporary password — you must set a new password now.')
                self.force_change_password(acc)
                self.current_account = acc
                self.open_dashboard()
            else:
                messagebox.showerror('Error', 'Invalid credentials')

        def force_change_password(self, acc):
            while True:
                new_pw = simpledialog.askstring('Set New Password', 'Enter new password:', show='*', parent=self.root)
                if new_pw is None:
                    return
                if len(new_pw) < 4:
                    messagebox.showerror('Error', 'Password must be at least 4 characters')
                    continue
                confirm = simpledialog.askstring('Set New Password', 'Confirm new password:', show='*', parent=self.root)
                if new_pw != confirm:
                    messagebox.showerror('Error', 'Passwords do not match')
                    continue
                change_password(self.accounts, acc, new_pw, self.accounts_file)
                messagebox.showinfo('Success', 'Password updated')
                return

        def forget_password(self):
            acc = simpledialog.askstring('Forget Password', 'Enter your account number:', parent=self.root)
            if not acc:
                return
            if acc not in self.accounts:
                messagebox.showerror('Error', 'Account not found')
                return
            temp = reset_password(self.accounts, acc, self.accounts_file)
            messagebox.showinfo('Temporary Password', f'Your temporary password is: {temp}\n\nUse it to login and change your password immediately.')

        def open_dashboard(self):
            if not self.current_account:
                return
            self.clear()
            acct = self.current_account
            frame_top = tk.Frame(self.root, bg=self.COLOR_HEADER)
            frame_top.pack(fill='x')
            tk.Label(frame_top, text=f'Account: {acct}', bg=self.COLOR_HEADER, fg='white', font=('Helvetica', 14, 'bold')).pack(side='left', padx=12, pady=10)
            tk.Label(frame_top, text=f"Name: {self.accounts[acct]['name']}", bg=self.COLOR_HEADER, fg='white', font=('Helvetica', 12)).pack(side='left', padx=12)

            body = tk.Frame(self.root, bg=self.COLOR_BG, padx=16, pady=12)
            body.pack(fill='both', expand=True)

            self.balance_var = tk.StringVar(value=f"Balance: {self.accounts[acct]['balance']:.2f}")
            tk.Label(body, textvariable=self.balance_var, bg=self.COLOR_BG, fg='#2d3748', font=('Helvetica', 12, 'bold')).pack(anchor='w')

            self.styled_button(body, 'Deposit', self.gui_deposit, bg=self.COLOR_ACCENT).pack(fill='x', pady=6)
            self.styled_button(body, 'Withdraw', self.gui_withdraw, bg=self.COLOR_WARN).pack(fill='x', pady=6)
            self.styled_button(body, 'Transfer', self.gui_transfer, bg=self.COLOR_PRIMARY).pack(fill='x', pady=6)
            self.styled_button(body, 'Change Password', lambda: self.gui_change_password(acct), bg='#6b46c1').pack(fill='x', pady=6)
            self.styled_button(body, 'Transaction History', self.gui_history, bg='#4a5568').pack(fill='x', pady=6)
            self.styled_button(body, 'Logout', self.logout, bg='#e53e3e').pack(fill='x', pady=6)

        def logout(self):
            self.current_account = None
            self.build_main_menu()

        def gui_deposit(self):
            amt = simpledialog.askstring('Deposit', 'Enter amount to deposit:', parent=self.root)
            try:
                val = float(amt)
                if val <= 0:
                    raise ValueError()
            except Exception:
                messagebox.showerror('Error', 'Invalid amount')
                return
            acc = self.current_account
            self.accounts[acc]['balance'] += val
            save_accounts(self.accounts, self.accounts_file)
            log_transaction(acc, 'Deposit', val, self.transactions_file)
            self.balance_var.set(f"Balance: {self.accounts[acc]['balance']:.2f}")
            messagebox.showinfo('Success', f'Deposited {val:.2f}')

        def gui_withdraw(self):
            amt = simpledialog.askstring('Withdraw', 'Enter amount to withdraw:', parent=self.root)
            try:
                val = float(amt)
                if val <= 0:
                    raise ValueError()
            except Exception:
                messagebox.showerror('Error', 'Invalid amount')
                return
            acc = self.current_account
            if self.accounts[acc]['balance'] < val:
                messagebox.showerror('Error', 'Insufficient funds')
                return
            self.accounts[acc]['balance'] -= val
            save_accounts(self.accounts, self.accounts_file)
            log_transaction(acc, 'Withdrawal', val, self.transactions_file)
            self.balance_var.set(f"Balance: {self.accounts[acc]['balance']:.2f}")
            messagebox.showinfo('Success', f'Withdrew {val:.2f}')

        def gui_transfer(self):
            to_acc = simpledialog.askstring('Transfer', 'Recipient account number:', parent=self.root)
            if not to_acc or to_acc not in self.accounts:
                messagebox.showerror('Error', 'Recipient not found')
                return
            amt = simpledialog.askstring('Transfer', 'Enter amount to transfer:', parent=self.root)
            try:
                val = float(amt)
                if val <= 0:
                    raise ValueError()
            except Exception:
                messagebox.showerror('Error', 'Invalid amount')
                return
            acc = self.current_account
            if self.accounts[acc]['balance'] < val:
                messagebox.showerror('Error', 'Insufficient funds')
                return
            self.accounts[acc]['balance'] -= val
            self.accounts[to_acc]['balance'] += val
            save_accounts(self.accounts, self.accounts_file)
            log_transaction(acc, 'Transfer Out', val, self.transactions_file)
            log_transaction(to_acc, 'Transfer In', val, self.transactions_file)
            self.balance_var.set(f"Balance: {self.accounts[acc]['balance']:.2f}")
            messagebox.showinfo('Success', f'Sent {val:.2f} to {to_acc}')

        def gui_change_password(self, acc):
            old_pw = simpledialog.askstring('Change Password', 'Enter current password:', show='*', parent=self.root)
            if old_pw is None:
                return
            if self.accounts[acc]['password'] != hash_password(old_pw):
                messagebox.showerror('Error', 'Incorrect current password')
                return
            new_pw = simpledialog.askstring('Change Password', 'Enter new password:', show='*', parent=self.root)
            confirm = simpledialog.askstring('Change Password', 'Confirm new password:', show='*', parent=self.root)
            if new_pw != confirm:
                messagebox.showerror('Error', 'Passwords do not match')
                return
            change_password(self.accounts, acc, new_pw, self.accounts_file)
            messagebox.showinfo('Success', 'Password changed')

        def gui_history(self):
            txs = get_transactions_for_account(self.current_account, self.transactions_file)
            win = tk.Toplevel(self.root)
            win.title('Transaction History')
            win.geometry('700x400')
            cols = ('Type', 'Amount', 'Date')
            tree = ttk.Treeview(win, columns=cols, show='headings')
            for c in cols:
                tree.heading(c, text=c)
            tree.pack(fill='both', expand=True)
            for row in txs:
                tree.insert('', 'end', values=(row.get('Type'), row.get('Amount'), row.get('DateTime')))

        def open_admin_panel(self):
            pw = simpledialog.askstring('Admin Panel', 'Enter admin password:', show='*', parent=self.root)
            if pw != ADMIN_PASSWORD:
                messagebox.showerror('Error', 'Access denied')
                return
            win = tk.Toplevel(self.root)
            win.title('Admin Panel')
            win.geometry('700x450')
            tree = ttk.Treeview(win, columns=('Account', 'Name', 'Balance'), show='headings')
            tree.heading('Account', text='Account')
            tree.heading('Name', text='Name')
            tree.heading('Balance', text='Balance')
            tree.pack(fill='both', expand=True)
            for acc, data in self.accounts.items():
                tree.insert('', 'end', values=(acc, data['name'], f"{data['balance']:.2f}"))

            def reset_selected():
                sel = tree.selection()
                if not sel:
                    messagebox.showerror('Error', 'Select a row')
                    return
                acc = str(tree.item(sel[0])['values'][0])
                temp = reset_password(self.accounts, acc, self.accounts_file)
                messagebox.showinfo('Temp Password', f'Temporary password for {acc}: {temp}')
                win.destroy()

            def delete_selected():
                sel = tree.selection()
                if not sel:
                    messagebox.showerror('Error', 'Select a row')
                    return
                acc = str(tree.item(sel[0])['values'][0])
                confirm = messagebox.askyesno('Confirm', f'Delete account {acc}?')
                if confirm:
                    delete_account(self.accounts, acc, self.accounts_file)
                    messagebox.showinfo('Deleted', f'Account {acc} deleted')
                    win.destroy()

            btn_frame = tk.Frame(win)
            btn_frame.pack(fill='x', pady=8)
            tk.Button(btn_frame, text='Reset Password', command=reset_selected, bg=self.COLOR_WARN, fg='white', bd=0, padx=8, pady=6).pack(side='left', padx=8)
            tk.Button(btn_frame, text='Delete Account', command=delete_selected, bg='#e53e3e', fg='white', bd=0, padx=8, pady=6).pack(side='left', padx=8)

class BankingCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.acc_file = os.path.join(self.tmpdir.name, 'accounts.txt')
        self.tx_file = os.path.join(self.tmpdir.name, 'transactions.txt')
        ensure_files(self.acc_file, self.tx_file)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_hash_password(self):
        pw = 'secret123'
        self.assertEqual(hash_password(pw), hashlib.sha256(pw.encode('utf-8')).hexdigest())

    def test_reset_and_temp_password(self):
        accounts = {}
        acc_id = '999999'
        accounts[acc_id] = {'name': 'TempUser', 'password': hash_password('orig'), 'balance': 0.0}
        save_accounts(accounts, self.acc_file)
        accounts_loaded = load_accounts(self.acc_file)
        temp = reset_password(accounts_loaded, acc_id, self.acc_file)
        loaded = load_accounts(self.acc_file)
        self.assertTrue(is_temp_password(loaded[acc_id]['password'], temp))
        
    from datetime import datetime  # already imported

def main_menu(self):
    try:
        while True:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n=== Banking System === ({now})")  # <-- shows date/time
            print('1. Create Account')
            print('2. Login')
            print('3. Forget Password')
            print('4. Admin Panel')
            print('5. Exit')
            choice = input('Enter choice: ').strip()
            if choice == '1':
                self.create_account_cli()
            elif choice == '2':
                self.login_cli()
            elif choice == '3':
                self.forget_password_cli()
            elif choice == '4':
                self.admin_panel_cli()
            elif choice == '5':
                print('Goodbye!')
                break
            else:
                print('Invalid choice')
    except (KeyboardInterrupt, EOFError):
        print('\nExiting...')


def run_tests():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(BankingCoreTests)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cli', action='store_true')
    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    if args.cli or not TK_AVAILABLE:
        BankingCLI().main_menu()
        return

    if args.gui and not TK_AVAILABLE:
        print('Tkinter not available — falling back to CLI')
        BankingCLI().main_menu()
        return

    root = tk.Tk()
    app = BankingGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()