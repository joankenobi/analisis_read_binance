from datetime import datetime
from logging_base import loge
from Binance_get_data import get_all_binance
import pandas as pd
from mongo_db_crud import Mongodb


class Backtecting:

    def __init__(self) -> None:
        pass



    def get_data_about_symbol(self, symbol=str, path=None):
        """Esta funcion retorna o actualiza el historial de precios de un simbolo determinado.

        Args:
            symbol (STR, optional): Idica la moneda a la cual se le va aplicar el proceso. Defaults to str.
            path (STR, optional): Direccions del historial de la moneda. Defaults to None.

        Returns:
            Data frame: Data frame del historial de precios del simbolo. 
        """
        df_symbol_data = get_all_binance(
            symbol=symbol, save=True, kline_size="5m")

        loge.info(f"Se creo el symbol_data {symbol}")
        return df_symbol_data



    def slice_df_by_date(self, df_symbol_data: pd.DataFrame, date_start: datetime, date_end: datetime = None):
        """Retorna un data frame sesgado entre dos fechas indicadas.

        Args:
            symbol_data (DataFrame): Idica el DataFrame al cual se quiere sesgar. Defaults to DataFrame.
            date_start (datetime): Tiempo más lejano para iniciar el sesgado. Defaults to Datetime.
            date_start (datetime, optional): Tiempo mas cercano para terminar el sesgado, si se coloca defaul este tiempo es simplemente la fecha del ultimo dato guardado. Defaults to None.


        Returns:
            Dataframe: Dataframe sesgado entre dos fechas dadas.
        """
        try:

            if df_symbol_data[df_symbol_data["date_myUTC"].apply(lambda x : x.year)==date_start.year].empty:

                # Busca los datosque pertenezcan a la fecha inicial para evitar un slice falso.
            
                loge.error("El df temp esta vacio por que los datos de la fecha no existe")
                raise Exception 

            if date_end == None:  # si no hay fecha de fin

                mask: pd.Series = df_symbol_data["date_myUTC"]

                loge.info(f"""date_start_by_sygnal: {str(date_start)}""")
                loge.info(
                    f"""last_date_symbol: {str(df_symbol_data["date_myUTC"].iloc[-1])}""")

                # Usa la fecha del ultimo dato guardado - Between no funcionaba con los str???? no se por que.
                mask = mask.between(
                    date_start, df_symbol_data["date_myUTC"].iloc[-1])

                temp_df_symbol: pd.DataFrame = df_symbol_data[mask]
                
                loge.info(
                    f"""symbol_data slice only start {str(date_start)} - {temp_df_symbol["date_myUTC"].iloc[-1]}""")
                return temp_df_symbol

            loge.info(f"""date_start: {str(date_start)}""")
            loge.info(f"""date_end: {str(date_end)}""")

            mask: pd.Series = df_symbol_data["date_myUTC"]
            mask = mask.between(date_start, date_end,)
            temp_df_symbol = df_symbol_data[mask]
            loge.info(f"symbol_data slice {str(date_start)} - {str(date_end)}")
            return temp_df_symbol
        
        except Exception as e:

            loge.error(f""" No hay forma de realizar slice, error: {e} """)
            exit()

            

    def find_entry_in_OHLC_line(self, entries_data, df_symbol_data: pd.DataFrame) -> dict:
        
        dates = {}

        # Convertir los datos numericos del precio en numeros flotantes.
        df_symbol_data.loc[:, ["open", "high", "low", "close"]] = df_symbol_data.loc[:, ["open", "high", "low", "close"]].astype(float)

        for operate in entries_data:

            # Objetivo: encontrar la vela en la que entró
            #loge.info(f"""df_symbol_data["open"]: {type(df_symbol_data["open"].iloc[0])}""")
            try:
                
                #loge.info(f"""df_symbol_data["open"]: {type(df_symbol_data["open"].iloc[0])}""")
                
                mask = (df_symbol_data["high"] >= operate) & (df_symbol_data["low"] <= operate) # el entry esta dentro de la vela? 
                                
                date = df_symbol_data[mask].iloc[0]["date_myUTC"] # La primera fila (tiempo mas lejano) que cumple la mask.

                if date:
                    dates[str(operate)] = date
                
            except Exception as e:

                loge.error(f""" No se encontro valor entry {operate} error: {e} """)
                dates[str(operate)] = bool(False)
                pass
        
        return dates






    def find_profit_in_OHLC_line(self, entries_data, df_symbol_data: pd.DataFrame,is_long=True) -> dict:
        """Consigue y compara los datos de entrada de operación con los precios indicados por el historial de precios.

        Args:
            entries_data: Precios de entrada para la operacion. Defaults to str.
            path (STR, optional): Direccions del historial de la moneda. Defaults to None. 

        Returns:
            Dict: Retorna un dictionary que contine los datos de operación evaluado y junto a este la fecha en la que el precio considió.
        """

        dates = {}

        # Convertir los datos numericos del precio en numeros flotantes.
        df_symbol_data.loc[:, ["open", "high", "low", "close"]] = df_symbol_data.loc[:, ["open", "high", "low", "close"]].astype(float)

        for operate in entries_data:

            #loge.info(f"""operate: {type(operate)}""")
            #loge.info(f"""df_symbol_data["open"]: {type(df_symbol_data["open"].iloc[0])}""")
            try:
                
                loge.info(f"""entry profit OHLC is_long: {is_long}""")
                #loge.info(f"""df_symbol_data["open"]: {type(df_symbol_data["open"].iloc[0])}""")
                
                if is_long:
                    mask = (df_symbol_data["open"] >= operate) | (df_symbol_data["high"] >= operate) | (
                    df_symbol_data["low"] >= operate) | (df_symbol_data["close"] >= operate)

                else:
                    mask = (df_symbol_data["open"] <= operate) | (df_symbol_data["high"] <= operate) | (df_symbol_data["low"] <= operate) | (df_symbol_data["close"] <= operate)
                    
                    
                
                # El primer valor (tiempo mas lejano) que cumple la mask.
                date = df_symbol_data[mask].iloc[0]["date_myUTC"]

                if date:
                    dates[str(operate)] = date
                
            except Exception as e:

                loge.error(f""" No se encontro valor profit {operate} error: {e} """)
                dates[str(operate)] = bool(False)
                pass
        return dates



    def find_stoploss_in_OHLC_line(self, stoploss_data, df_symbol_data: pd.DataFrame, is_long=True) -> dict:
        """Consigue y compara los datos de operación con los precios indicados por el historial de precios.

        Args:
            stoploss_data: Indica el precio de salida para evitar perdidas. Defaults to str.
            path (STR, optional): Direccions del historial de la moneda. Defaults to None. 

        Returns:
            Dict: Retorna un dictionary que contine los datos de operación evaluado y junto a este la fecha en la que el precio considió.
        """

        dates = {}

        # Convertir los datos numericos del precio en numeros flotantes.
        df_symbol_data.loc[:, ["open", "high", "low", "close"]] = df_symbol_data.loc[:, [
            "open", "high", "low", "close"]].astype(float)

        for operate in stoploss_data:
            
            try:

                loge.info(f"""stop loss OHLC is_long: {is_long}""")
                #loge.info(f"""df_symbol_data["open"]: {type(df_symbol_data["open"].iloc[0])}""")
                if is_long:
                    mask = (df_symbol_data["open"] <= operate) | (df_symbol_data["high"] <= operate) | (df_symbol_data["low"] <= operate) | (df_symbol_data["close"] <= operate)

                else:
                    mask = (df_symbol_data["open"] >= operate) | (df_symbol_data["high"] >= operate) | (df_symbol_data["low"] >= operate) | (df_symbol_data["close"] >= operate)

                # El primer valor (tiempo mas lejano) que cumple la mask.
                date = df_symbol_data[mask].iloc[0]["date_myUTC"]

                if date:
                    dates[str(operate)] = date
            
            except Exception as e:
                loge.error(f""" No se encontro valor {operate} error: {e} """)
                dates[str(operate)] = bool(False)
                pass
        
        return dates



    def update_backtesting(self, _id, tagname, set, host="mongodb://localhost:27017/", collection="signals"):
        """Actualiza automaticamente los datos en la base de datos.
        """

        Mongodb().update_by_id(collection, _id, tagname, set)



    def backtest_operate(self, df_sygnal_data: pd.DataFrame, data_base="DB_test"):
        """Ejecuta todo el proceso de backtesting

        arg:
            df_sygnal_data (DataFrame): Indica el dataframe del historial de precios  del simbolo de la operación. Defaults to DataFrame.
            data_base (STR, opcional): Indica el nombre de la base de datos a actualizar. Defaults to "DB_test"

        """

        for i in range(len(df_sygnal_data)):

        
        ### Get symbol data

            loge.info(
                f"""get symbol data nro: {i} {df_sygnal_data.loc[i,"symbol"]}""")

            df_symbol_data = self.get_data_about_symbol(
                df_sygnal_data.loc[i, "symbol"])

            is_long=df_sygnal_data.iloc[i]["is_long"]
        
        
        #### Get date entry
            date_start = df_sygnal_data.loc[i, "date"]

            temp_df_symbol = self.slice_df_by_date(
                df_symbol_data=df_symbol_data, date_start=date_start)
            entry_targets = df_sygnal_data.iloc[i]["entry_targets"]

            loge.info(
                f"""entry_targets: {entry_targets} Type:  {type(entry_targets)}""")

            dates_entry: dict = self.find_entry_in_OHLC_line(
                entries_data=entry_targets, df_symbol_data=temp_df_symbol)
            
            loge.info(f"dates_entry: {dates_entry}")
        
        
        
        ### Get date stoploss
            date_start = list(dates_entry.values())[0]
            temp_df_symbol = self.slice_df_by_date(
                df_symbol_data=temp_df_symbol, date_start=date_start)

            stop_targets = df_sygnal_data.iloc[i]["stop_targets"]

            loge.info(
                f"""stop_targets: {stop_targets} Type:  {type(stop_targets)}""")
            

            dates_stoploss: dict = self.find_stoploss_in_OHLC_line(
                stoploss_data=stop_targets, df_symbol_data=temp_df_symbol,is_long=is_long)
            loge.info(f"dates_stoploss: {dates_stoploss}")

        
        
        ### Get dates_profit
            dates_end = list(dates_stoploss.values())[0]
            
            temp_df_symbol = self.slice_df_by_date(
                df_symbol_data=temp_df_symbol, date_start=date_start, date_end=dates_end)
            
            take_profit_targets = df_sygnal_data.iloc[i]["take_profit_targets"]
            
            loge.info(
                f"""take_profit_targets: {take_profit_targets} Type:  {type(take_profit_targets)}""")
            
            dates_profit: dict = self.find_profit_in_OHLC_line(
                entries_data=take_profit_targets, df_symbol_data=temp_df_symbol,is_long=is_long)
            
            loge.info(f"dates_profit: {dates_profit}")
            
            
        #### Get efficiency
            efficiency={f"""{(len(list(dates_profit.values()))-list(dates_profit.values()).count(False))}/{len(list(dates_profit.values()))} """:(len(list(dates_profit.values()))-list(dates_profit.values()).count(False))/len(list(dates_profit.values()))}

            
        ### Update db
            loge.info(f"""df_sygnal_data.loc[i,"_id"]: {df_sygnal_data.loc[i,"_id"]}""")
            #loge.info(f"""df_sygnal_data.loc[i,"_id"]["$oid"]: {df_sygnal_data.loc[i,"_id"]["$oid"]}""")
            _id=df_sygnal_data.loc[i,"_id"]
            self.update_backtesting(_id,"dates_entry",dates_entry)
            self.update_backtesting(_id,"dates_stoploss",dates_stoploss)
            self.update_backtesting(_id,"dates_profit",dates_profit)
            self.update_backtesting(_id,"efficiency",efficiency)
        print("all line backteting.....")


if __name__ == "__main__":

    host = "mongodb://localhost:27017/"
    db_name = "back_prueba"
    db = Mongodb(host).set_db(db_name)
    data = db.signals.find()
    list_data = list(data)
    df_sygnal_data = pd.DataFrame(list_data)
    Backtecting().backtest_operate(df_sygnal_data, db_name)
