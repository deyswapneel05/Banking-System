# Banking System Project

## 📌 Overview

This project is a **Banking System developed in Python** that simulates
core banking operations such as account creation, deposit, withdrawal,
transfer, password management, and transaction history.

It supports both **Command-Line Interface (CLI)** and **Graphical User
Interface (GUI)** modes, making it versatile for different users.

------------------------------------------------------------------------

## ✨ Features

-   **Account Management**
    -   Create account with name, password, and initial deposit.
    -   Passwords are securely stored using SHA-256 hashing.
-   **Banking Operations**
    -   Deposit, withdraw, and transfer funds between accounts.
    -   Real-time balance updates.
-   **Transaction History**
    -   Every transaction is recorded with **date and time**.
-   **Password Management**
    -   Forgot password feature with temporary password generation.
    -   Option to reset password upon login.
-   **Admin Panel**
    -   View all accounts with balance.
    -   Reset passwords or delete accounts securely.
-   **Date & Time Display**
    -   Shows current date and time on main menu and dashboard.
-   **Unit Testing**
    -   Includes `unittest` test cases for critical features like
        password hashing and reset.

------------------------------------------------------------------------

## 🖥 Modes of Operation

1.  **CLI Mode**

    -   Run the program with:

    ``` bash
    python banking_system.py --cli
    ```

    -   Works in any terminal.

2.  **GUI Mode**

    -   Run the program with:

    ``` bash
    python banking_system.py --gui
    ```

    -   Provides an interactive Tkinter-based interface.

3.  **Run Tests**

    ``` bash
    python banking_system.py --test
    ```

------------------------------------------------------------------------

## 🗂 File Structure

    ├── banking_system.py        # Main program file
    ├── accounts.txt             # Stores account data
    ├── transactions.txt         # Stores transaction logs
    ├── README.md                # Project documentation

------------------------------------------------------------------------

## ⚙️ Requirements

-   Python 3.x
-   Tkinter (for GUI mode)

------------------------------------------------------------------------

## 🚀 How to Run

1.  Ensure `accounts.txt` and `transactions.txt` exist (created
    automatically if missing).
2.  Run the program using CLI or GUI mode.
3.  Create an account, login, and perform transactions.

------------------------------------------------------------------------

## 🎯 Conclusion

This project demonstrates: - File handling - Data security with password
hashing - GUI development with Tkinter - Persistent storage using CSV
files - Software testing using unittest

It is a complete **banking system simulation** that is secure, reliable,
and user-friendly.
