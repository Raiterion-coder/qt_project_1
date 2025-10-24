
import sys, csv
from datetime import datetime
from pathlib import Path

from PyQt5 import QtWidgets, QtCore, QtGui, uic
from app.database import Database

def resource(rel): return str(QtCore.QDir.current().filePath(rel))

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/main_window.ui', self)
        self.db = Database()

        # <-- ДОБАВЛЯЕМ ВОТ ЭТО
        self.tblAccounts.setColumnCount(2)
        self.tblAccounts.setHorizontalHeaderLabels(["Название", "Баланс"])
        self.tblAccounts.horizontalHeader().setStretchLastSection(True)
        self.tblAccounts.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tblAccounts.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.tblTransactions.setColumnCount(5)
        self.tblTransactions.setHorizontalHeaderLabels(["Дата", "Счёт", "Категория", "Сумма", "Комментарий"])
        self.tblTransactions.horizontalHeader().setStretchLastSection(True)
        self.tblTransactions.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tblTransactions.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        # остальное как было
        self.refresh_tables()
        self.btnAddAccount.clicked.connect(self.add_account)
        self.btnAddTx.clicked.connect(self.on_add_transaction)
        self.btnShowImage.clicked.connect(self.show_image)

    def refresh_tables(self):
        accs = self.db.list_accounts()
        self.tblAccounts.setRowCount(0)
        for i,a in enumerate(accs):
            self.tblAccounts.insertRow(i)
            self.tblAccounts.setItem(i,0,QtWidgets.QTableWidgetItem(a['name']))
            self.tblAccounts.setItem(i,1,QtWidgets.QTableWidgetItem(str(a['balance'])))
        txs = self.db.list_transactions()
        self.tblTransactions.setRowCount(0)
        for i,t in enumerate(txs):
            self.tblTransactions.insertRow(i)
            self.tblTransactions.setItem(i,0,QtWidgets.QTableWidgetItem(t['date']))
            self.tblTransactions.setItem(i,1,QtWidgets.QTableWidgetItem(t['account']))
            self.tblTransactions.setItem(i,2,QtWidgets.QTableWidgetItem(t['category']))
            self.tblTransactions.setItem(i,3,QtWidgets.QTableWidgetItem(str(t['amount'])))
            self.tblTransactions.setItem(i,4,QtWidgets.QTableWidgetItem(t['comment']))

    def add_account(self):
        name, ok = QtWidgets.QInputDialog.getText(self, 'Добавить счёт', 'Название счёта:')
        if not ok or not name.strip():
            return

        balance, ok = QtWidgets.QInputDialog.getDouble(self, 'Начальный баланс', 'Введите начальный баланс:', 0.0,
                                                       -999999999, 999999999, 2)
        if not ok:
            return

        self.db.add_account(name.strip(), balance)
        self.refresh_tables()

    def on_add_transaction(self):
        dlg = QtWidgets.QDialog(self)
        uic.loadUi(str(Path(__file__).parent / "ui" / "add_transaction.ui"), dlg)

        dateEdit = dlg.findChild(QtWidgets.QDateEdit, "dateEdit")
        cmbAccount = dlg.findChild(QtWidgets.QComboBox, "cmbAccount")
        edtCategory = dlg.findChild(QtWidgets.QLineEdit, "edtCategory")
        spinAmount = dlg.findChild(QtWidgets.QDoubleSpinBox, "spinAmount")
        edtComment = dlg.findChild(QtWidgets.QLineEdit, "edtComment")
        buttonBox = dlg.findChild(QtWidgets.QDialogButtonBox, "buttonBox")

        # Загружаем счета
        accounts = self.db.list_accounts()
        for a in accounts:
            cmbAccount.addItem(a["name"], a["id"])

        def handle_accept():
            date = dateEdit.date().toString("yyyy-MM-dd")
            account_id = cmbAccount.currentData()
            category = edtCategory.text().strip()
            amount = float(spinAmount.value())
            comment = edtComment.text().strip()

            if account_id is None:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите счёт")
                return
            if amount == 0:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Сумма не может быть 0")
                return

            rbtnExpense = dlg.findChild(QtWidgets.QRadioButton, "rbtnExpense")
            rbtnIncome = dlg.findChild(QtWidgets.QRadioButton, "rbtnIncome")

            if rbtnIncome and rbtnIncome.isChecked():
                delta = +amount
            else:
                delta = -amount

            self.db.add_transaction(date, account_id, category, amount, comment)
            self.db.update_account_balance(account_id, delta)
            dlg.accept()

        buttonBox.accepted.connect(handle_accept)
        buttonBox.rejected.connect(dlg.reject)

        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.refresh_tables()


    def show_image(self):
        img = QtGui.QPixmap('app/resources/sample.png')
        lbl = QtWidgets.QLabel()
        lbl.setPixmap(img.scaled(600,400,QtCore.Qt.KeepAspectRatio))
        dlg = QtWidgets.QDialog(self)
        layout = QtWidgets.QVBoxLayout(dlg)
        layout.addWidget(lbl)
        dlg.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
