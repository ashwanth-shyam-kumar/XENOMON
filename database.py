import mysql.connector


class DBManager:
    def __init__(self, host, user, password, database):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.connection.cursor()

    def save_player_progress(self, player_id, pos, monsters):
        # Save player position
        self.cursor.execute(
    "INSERT INTO player_progress (player_id, pos_x, pos_y) VALUES (%s, %s, %s) "
    "ON DUPLICATE KEY UPDATE pos_x=VALUES(pos_x), pos_y=VALUES(pos_y)",
    (player_id, pos[0], pos[1])
    )


        # Delete existing monsters for this player and insert updated data
        self.cursor.execute("DELETE FROM monsters WHERE player_id=%s", (player_id,))
        for monster in monsters.values():
            self.cursor.execute(
                "INSERT INTO monsters (player_id, name, level, xp, fainted, health, energy) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (player_id, monster.name, monster.level, monster.xp, monster.fainted, monster.health, monster.energy)
            )

        self.connection.commit()

    def load_player_progress(self, player_id):
        self.cursor.execute("SELECT pos_x, pos_y FROM player_progress WHERE player_id=%s", (player_id,))
        pos = self.cursor.fetchone()
        self.cursor.execute("SELECT name, level, xp, fainted, health, energy FROM monsters WHERE player_id=%s", (player_id,))
        monsters_data = self.cursor.fetchall()
        return pos, monsters_data

    def save_trainer_status(self, player_id, trainer_id, defeated):
        self.cursor.execute(
            "INSERT INTO trainer_status (player_id, trainer_id, defeated) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE defeated=VALUES(defeated)",
            (player_id, trainer_id, defeated)
        )
        self.connection.commit()

    def load_trainer_status(self, player_id):
        self.cursor.execute("SELECT trainer_id, defeated FROM trainer_status WHERE player_id=%s", (player_id,))
        return dict(self.cursor.fetchall())


    def close(self):
        self.cursor.close()
        self.connection.close()
