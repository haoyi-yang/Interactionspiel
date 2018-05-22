import sqlite3 as lite




class database_operation:

    table_name = "gameinfotbl"
    standard_insert = "Player_name, win_rate, hole_cards, community_cards, action, stack, small_blind_amount"


    def __init__(self, db_name):

        self.db_name = db_name

        con = lite.connect(self.db_name)

        with con:
            cur = con.cursor()

            cur.execute("CREATE TABLE IF NOT EXISTS {tbl_name}(_Id INTEGER PRIMARY KEY, Player_name TEXT, win_rate REAL,  \
                                                                hole_cards TEXT, community_cards TEXT, action INT, stack INT, small_blind_amount INT)".format(tbl_name = gameinfotbl))

            


    def record_game_information(self, msg_record):
        con = lite.connect(self.db_name)

        with con:
            cur = con.cursor()

            cur.execute("INSERT INTO {tbl_name}({std_ins}) VALUES(?,?,?,?,?,?,?)", msg_record)



    def 





    # def create_new_infomation_database(name):
    
    #     con = None

    #     try:
    #         con = lite.connect(name)

    #     finally:
    #         if con:
    #             con.close()


    
    def 