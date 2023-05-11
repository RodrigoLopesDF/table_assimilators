import pandas as pd
import Levenshtein as lvs

class Formatter:
    def __init__(self,table:"pd.DataFrame",column:str, default_lvs_weight=25) -> None:
        
        self.column = column
        self.table = table.sort_values(column).reset_index(drop=True)
        self.default_lvs_weight = default_lvs_weight
        self.words = table[column].tolist()

    def get_assimilated_params(self,max_weight=None,use_nearby_columns_as_reference=False,columns=[]):
        if(use_nearby_columns_as_reference):
            if not columns:
                return self.get_assimilated_params(max_weight)

        if max_weight == None:
            max_weight = self.default_lvs_weight

        assimilated_results = []
        was_assimilated = []
        corrections_manual = {}

        for line in range(len(self.table.index)):
            
            row = self.table.iloc[line]
            key_phrase = row[self.column]
            if key_phrase in was_assimilated:
                continue
            else:
                assimilated_results.append(key_phrase)

            for other_line in range(line+1,len(self.table.index)):

                other_row = self.table.iloc[other_line]
                other_phrase = other_row[self.column]
                if other_phrase in was_assimilated:
                    continue

                if use_nearby_columns_as_reference:
                    reference_match = True
                    for reference in columns:
                        if(other_row[reference] != row[reference]):
                            reference_match = False
                            break

                    if not reference_match:
                        continue
                
                distance = lvs.distance(key_phrase,other_phrase)
                if(distance > max_weight):

                    was_assimilated.append(other_phrase)
                    if(corrections_manual.get(key_phrase) is None):
                        corrections_manual[key_phrase] = [other_phrase]
                    else:
                        corrections_manual[key_phrase].append(other_phrase)
        
        return assimilated_results,corrections_manual 

    def get_assimilated_table(self, max_weight=None, use_nearby_columns_as_reference=False, columns=[]):
        if max_weight == None:
            max_weight = self.default_lvs_weight

        assimilated_results, corrections_manual = self.get_assimilated_params(max_weight, use_nearby_columns_as_reference, columns)
        new_table = self.table[self.table[self.column].isin(assimilated_results)].copy()
        ordered_table = new_table.sort_values(self.column).reset_index(drop=True)

        self.previous_weight = max_weight
        self.previous_assimilated_table = ordered_table
        self.previous_correction_manual = corrections_manual
        
        return ordered_table, corrections_manual

    def _fully_assimilate(self):
        references = self.table.columns.to_numpy()
        references = references[references != self.column].tolist()

        return self.get_assimilated_table(use_nearby_columns_as_reference=True,columns=references)

    def correct_table(self,table:pd.DataFrame):
        if not self.column in table.columns:
            return table

        _,manual = self._fully_assimilate()
        corrected_values = [element for inner_list in manual.values() for element in inner_list]
        history = []

        selected_rows = []
        for _,row in table.iterrows():
            new_row = row.copy()
            value = row[self.column]

            if value in history:
                continue

            if value in corrected_values:
                for key,values in manual:
                    if value in values:
                        new_row[self.column] = key
                        break

            new_value = row[self.column]
            if new_value in history:
                continue 

            selected_rows.append(new_row)
            history.append(new_value)
        formatted_table = pd.DataFrame(selected_rows)
        formatted_table = formatted_table.sort_values(self.column).reset_index(drop=True)
        return formatted_table

    def __str__(self) -> str:

        references = self.table.columns.to_numpy()
        references = references[references != self.column].tolist()
        result_table,_ = self.get_assimilated_table(use_nearby_columns_as_reference=True,columns=references)

        return result_table.to_string(index=False)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, pd.DataFrame):
            if self.column not in __o:
                return False
            __o = Formatter(__o, self.column)
        if isinstance(__o, Formatter):
            return str(self) == str(__o)
        return False

    def __sizeof__(self) -> int:
        references = self.table.columns.to_numpy()
        references = references[references != self.column].tolist()
        result_table,_ = self.get_assimilated_table(use_nearby_columns_as_reference=True,columns=references)
        
        return len(result_table.index)