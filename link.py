import itertools

class Link:

    newid = itertools.count()

    def __init__(self, transactions, quantity) -> None:

        self.id = next(Link.newid)
        self.transactions = sorted(transactions, key=lambda transaction: transaction.trans_type)
        self.quantity = quantity
        self.trans1 = self.transactions[0]
        self.trans2 = self.transactions[1]

        if self.transactions[0].trans_type == 'buy':
            self.buy = self.trans1
            self.sell = self.trans2
        
        elif self.transactions[0].trans_type == 'sell':
            self.buy = self.trans2
            self.sell = self.trans1

        self.symbol = self.sell.symbol

        if self.buy.unlinked_quantity < 0 or self.sell.unlinked_quantity < 0:
            print(f"Cannot link because quantity unlinked is less than 0")

        self.link_buy_price = (quantity * self.trans1.usd_spot)
        self.link_sell_price = (quantity * self.trans2.usd_spot)
        self.link_sell_date = self.trans2.time_stamp
        self.link_buy_date = self.trans1.time_stamp
        self.profit_loss = (self.link_sell_price - self.link_buy_price)


    def __hash__(self) -> int:
        return hash(tuple(self.transactions))

    def __str__(self) -> str:
        return f"Name: [{self.transactions[0].name}] Trans Type [{self.transactions[0].trans_type}] Quantity [{self.transactions[0].quantity:.2f}]\
        <-{self.quantity:.2f}-> \
        Name: [{self.transactions[1].name}] Trans Type [{self.transactions[1].trans_type}] Quantity [{self.transactions[1].quantity:.2f}]"

    def __repr__(self):
        return f"Link ID: {self.id} Link Quantity: {self.quantity}"


    @property
    def hodl_duration(self):
        hodl_time =  self.sell.time_stamp - self.buy.time_stamp

        return hodl_time


    @property
    def proceeds(self):
        return self.quantity * self.sell.usd_spot

    @property
    def cost_basis(self):
        return self.quantity * self.buy.usd_spot

    def other_transaction(self, trans):
        if trans == self.trans1:
            return self.trans2.name
        else:
            return self.trans1.name


if __name__ == '__main__':
    test_link = Link()