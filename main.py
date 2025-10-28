import sys, shutil
from datetime import datetime
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
import matplotlib.pyplot as plt
from app.database import Database, PHOTO_DIR
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


def resource(rel):
    return str(QtCore.QDir.current().filePath(rel))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui/main_window.ui', self)
        self.db = Database()

        # --- Настройка таблиц ---
        self.tblAccounts.setColumnCount(2)
        self.tblAccounts.setHorizontalHeaderLabels(["Название", "Баланс"])
        self.tblAccounts.horizontalHeader().setStretchLastSection(True)
        self.tblAccounts.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tblAccounts.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.btnShowChart.clicked.connect(self.show_chart)

        self.tblTransactions.setColumnCount(6)
        self.tblTransactions.setHorizontalHeaderLabels(["Дата", "Счёт", "Категория", "Сумма", "Комментарий", "Фото"])
        self.tblTransactions.horizontalHeader().setStretchLastSection(True)
        self.tblTransactions.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tblTransactions.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        # --- Кнопки ---
        self.refresh_tables()
        self.btnAddAccount.clicked.connect(self.add_account)
        self.btnAddTx.clicked.connect(self.on_add_transaction)
        self.btnShowImage.clicked.connect(self.show_image)
        self.btnDelAccount.clicked.connect(self.delete_account)
        self.btnDelTx.clicked.connect(self.delete_transaction)

    # ------------------- ОБНОВЛЕНИЕ -------------------

    def refresh_tables(self):
        accs = self.db.list_accounts()
        self.tblAccounts.setRowCount(0)
        for i, a in enumerate(accs):
            self.tblAccounts.insertRow(i)
            self.tblAccounts.setItem(i, 0, QtWidgets.QTableWidgetItem(a['name']))
            self.tblAccounts.setItem(i, 1, QtWidgets.QTableWidgetItem(str(a['balance'])))

        txs = self.db.list_transactions()
        self.tblTransactions.setRowCount(0)
        for i, t in enumerate(txs):
            self.tblTransactions.insertRow(i)
            self.tblTransactions.setItem(i, 0, QtWidgets.QTableWidgetItem(t['date']))
            self.tblTransactions.setItem(i, 1, QtWidgets.QTableWidgetItem(t['account']))
            self.tblTransactions.setItem(i, 2, QtWidgets.QTableWidgetItem(t['category']))
            self.tblTransactions.setItem(i, 3, QtWidgets.QTableWidgetItem(str(t['amount'])))
            self.tblTransactions.setItem(i, 4, QtWidgets.QTableWidgetItem(t['comment']))
            self.tblTransactions.setItem(i, 5, QtWidgets.QTableWidgetItem("📷" if t['photo_path'] else "-"))

    # ------------------- ДОБАВЛЕНИЕ СЧЁТА -------------------

    def add_account(self):
        name, ok = QtWidgets.QInputDialog.getText(self, 'Добавить счёт', 'Название счёта:')
        if not ok or not name.strip():
            return

        balance, ok = QtWidgets.QInputDialog.getDouble(
            self, 'Начальный баланс', 'Введите начальный баланс:', 0.0,
            -999999999, 999999999, 2
        )
        if not ok:
            return

        self.db.add_account(name.strip(), balance)
        self.refresh_tables()

    # ------------------- УДАЛЕНИЕ СЧЁТА -------------------
    from PyQt5 import QtWidgets
    import matplotlib.pyplot as plt

    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure

    def show_chart(self):
        accounts = self.db.list_accounts()
        if not accounts:
            QtWidgets.QMessageBox.warning(self, "Нет счетов", "Сначала создайте хотя бы один счёт.")
            return

        items = [f"{a['id']} - {a['name']}" for a in accounts]
        item, ok = QtWidgets.QInputDialog.getItem(self, "Выбор счёта", "Выберите счёт:", items, 0, False)
        if not ok or not item:
            return

        selected_id = int(item.split(" - ")[0])
        txs = [t for t in self.db.list_transactions() if t["id"] and t["account"] and self.db.conn.execute(
            "SELECT id FROM accounts WHERE name=?", (t["account"],)
        ).fetchone()["id"] == selected_id]

        if not txs:
            QtWidgets.QMessageBox.information(self, "Нет данных", "Для выбранного счёта нет транзакций.")
            return

        daily = {}
        for t in txs:
            d = t["date"]
            amt = float(t["amount"])
            daily[d] = daily.get(d, 0) + amt

        try:
            dates = [datetime.strptime(d, "%Y-%m-%d") for d in sorted(daily.keys())]
        except Exception:
            dates = sorted(daily.keys())

        balance = []
        cur = 0
        for d in sorted(daily.keys()):
            cur += daily[d]
            balance.append(cur)

        account = next((a for a in accounts if a["id"] == selected_id), None)

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"График счёта: {account['name']}")
        dialog.resize(900, 600)

        fig = Figure(figsize=(9, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(canvas)

        ax.plot(dates, balance, marker='o', linestyle='-', linewidth=2)
        ax.grid(True)
        ax.set_title(f"Изменение баланса: {account['name']}")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Баланс")

        canvas.draw()
        dialog.exec_()

    def delete_account(self):
        row = self.tblAccounts.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите счёт для удаления")
            return

        name = self.tblAccounts.item(row, 0).text()

        reply = QtWidgets.QMessageBox.question(
            self, "Подтверждение",
            f"Удалить счёт '{name}' и все связанные транзакции?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return

        self.db.conn.execute("DELETE FROM transactions WHERE account_id = (SELECT id FROM accounts WHERE name=?)",
                             (name,))
        self.db.conn.execute("DELETE FROM accounts WHERE name=?", (name,))
        self.db.conn.commit()

        self.refresh_tables()
        QtWidgets.QMessageBox.information(self, "Готово", f"Счёт '{name}' удалён.")

    # ------------------- ДОБАВЛЕНИЕ ТРАНЗАКЦИИ -------------------

    def on_add_transaction(self):
        dlg = QtWidgets.QDialog(self)
        uic.loadUi(str(Path(__file__).parent / "ui" / "add_transaction.ui"), dlg)

        dateEdit = dlg.findChild(QtWidgets.QDateEdit, "dateEdit")
        cmbAccount = dlg.findChild(QtWidgets.QComboBox, "cmbAccount")
        edtCategory = dlg.findChild(QtWidgets.QLineEdit, "edtCategory")
        spinAmount = dlg.findChild(QtWidgets.QDoubleSpinBox, "spinAmount")
        edtComment = dlg.findChild(QtWidgets.QLineEdit, "edtComment")
        buttonBox = dlg.findChild(QtWidgets.QDialogButtonBox, "buttonBox")
        btnAddPhoto = dlg.findChild(QtWidgets.QPushButton, "btnAddPhoto")
        btnOpenPhoto = dlg.findChild(QtWidgets.QPushButton, "btnOpenPhoto")
        lblPhotoPath = dlg.findChild(QtWidgets.QLabel, "lblPhotoPath")

        photo_path = None

        # Загружаем счета
        accounts = self.db.list_accounts()
        for a in accounts:
            cmbAccount.addItem(a["name"], a["id"])

        # Выбор фото
        def select_photo():
            nonlocal photo_path
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Выберите фото", "", "Изображения (*.png *.jpg *.jpeg *.bmp)"
            )
            if file_path:
                dest = PHOTO_DIR / Path(file_path).name
                try:
                    shutil.copy(file_path, dest)
                    photo_path = str(dest)
                    lblPhotoPath.setText(Path(file_path).name)
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось скопировать файл:\n{e}")

        # Открытие фото
        def open_photo():
            if photo_path and Path(photo_path).exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(photo_path))
            else:
                QtWidgets.QMessageBox.warning(self, "Фото", "Фото не выбрано или не найдено.")

        btnAddPhoto.clicked.connect(select_photo)
        btnOpenPhoto.clicked.connect(open_photo)

        # Обработка OK
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

            # 💥 Вот ключевой момент
            if rbtnExpense.isChecked():
                amount = -abs(amount)  # расход -> отрицательное число
            else:
                amount = abs(amount)  # доход -> положительное число

            self.db.add_transaction(date, account_id, category, amount, comment, photo_path)
            self.db.update_account_balance(account_id, amount)
            dlg.accept()

        buttonBox.accepted.connect(handle_accept)
        buttonBox.rejected.connect(dlg.reject)

        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.refresh_tables()

    # ------------------- УДАЛЕНИЕ ТРАНЗАКЦИИ -------------------

    def delete_transaction(self):
        row = self.tblTransactions.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите транзакцию для удаления")
            return

        date = self.tblTransactions.item(row, 0).text()
        account = self.tblTransactions.item(row, 1).text()
        category = self.tblTransactions.item(row, 2).text()
        amount = float(self.tblTransactions.item(row, 3).text())

        reply = QtWidgets.QMessageBox.question(
            self, "Подтверждение",
            f"Удалить транзакцию '{category}' ({amount})?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return

        # Получаем account_id
        cur = self.db.conn.cursor()
        cur.execute("SELECT id FROM accounts WHERE name=?", (account,))
        acc = cur.fetchone()
        if not acc:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Счёт не найден")
            return

        account_id = acc["id"]

        # Удаляем транзакцию
        cur.execute("""
            DELETE FROM transactions 
            WHERE date=? AND account_id=? AND category=? AND amount=?
        """, (date, account_id, category, amount))
        self.db.conn.commit()

        # Возврат суммы на счёт
        self.db.update_account_balance(account_id, -amount)

        self.refresh_tables()
        QtWidgets.QMessageBox.information(self, "Готово", "Транзакция удалена.")

    # ------------------- ПРОСМОТР ИЗОБРАЖЕНИЯ -------------------

    def show_image(self):
        row = self.tblTransactions.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите транзакцию")
            return

        date = self.tblTransactions.item(row, 0).text()
        account = self.tblTransactions.item(row, 1).text()
        category = self.tblTransactions.item(row, 2).text()
        amount = float(self.tblTransactions.item(row, 3).text())

        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT t.photo_path FROM transactions t
            JOIN accounts a ON a.id = t.account_id
            WHERE t.date=? AND a.name=? AND t.category=? AND t.amount=?
        """, (date, account, category, amount))
        row = cur.fetchone()

        if row and row["photo_path"] and Path(row["photo_path"]).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(row["photo_path"]))
        else:
            QtWidgets.QMessageBox.information(self, "Фото", "Фото не найдено для этой транзакции.")


# ------------------- ЗАПУСК -------------------

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
