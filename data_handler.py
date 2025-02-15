import csv
import io
import requests
from typing import List, Dict, Any, Optional

class DataHandler:
    @staticmethod
    def fetch_sheet_data(sheet_url: str, gid: int) -> Optional[List[Dict[str, Any]]]:
        try:
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
            response = requests.get(export_url)
            if response.status_code != 200:
                return None
            
            csv_content = io.StringIO(response.text)
            reader = csv.DictReader(csv_content)
            return list(reader)
            
        except Exception as e:
            print(f"Error fetching sheet: {e}")
            return None

    @staticmethod
    def get_round1_sort_key(row: Dict[str, Any]) -> tuple:
        """Round 1 sorting logic: completion > time > moves"""
        status = str(row.get('Status', '')).lower()
        is_complete = 'complete' in status
        
        try:
            if ':' in str(row.get('Time', '')):
                mins, secs = map(int, row['Time'].split(':'))
                time_score = mins * 60 + secs
            else:
                time_score = 999999
        except:
            time_score = 999999
            
        try:
            moves = int(str(row.get('Moves', '999')).strip() or '999')
        except:
            moves = 999
            
        try:
            accuracy = float(str(row.get('Accuracy', '0')).rstrip('%') or '0')
        except:
            accuracy = 0
            
        if is_complete:
            return (0, time_score, moves)  # Completed runs: sort by time, then moves
        else:
            return (1, -accuracy, moves)   # Timeout runs: sort by accuracy, then moves

    @staticmethod
    def sort_round1(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sorted_data = sorted(data, key=DataHandler.get_round1_sort_key)
        for i, row in enumerate(sorted_data, 1):
            row['Rank'] = str(i)
        return sorted_data

    @staticmethod
    def sort_round2(data: List[Dict[str, Any]], round1_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Round 2: Sort by score, then Round 1 performance"""
        round1_dict = {row['Team Name']: row for row in round1_data}
        
        def get_sort_key(row):
            team_name = row['Team Name']
            try:
                score = float(str(row.get('Score', '0')).strip() or '0')
            except:
                score = 0
            
            # Get Round 1 tiebreaker
            r1_key = DataHandler.get_round1_sort_key(round1_dict.get(team_name, {}))
            return (-score, *r1_key)  # Negative score for descending order
            
        sorted_data = sorted(data, key=get_sort_key)
        for i, row in enumerate(sorted_data, 1):
            row['Rank'] = str(i)
        return sorted_data

    @staticmethod
    def sort_round3(data: List[Dict[str, Any]], round2_data: List[Dict[str, Any]], 
                    round1_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Round 3: Sort by score, then R2 score, then R1 performance"""
        round2_dict = {row['Team Name']: row for row in round2_data}
        round1_dict = {row['Team Name']: row for row in round1_data}
        
        def get_sort_key(row):
            team_name = row['Team Name']
            try:
                score = float(str(row.get('Score', '0')).strip() or '0')
            except:
                score = 0
                
            # Get Round 2 score
            try:
                r2_score = float(str(round2_dict.get(team_name, {}).get('Score', '0')).strip() or '0')
            except:
                r2_score = 0
                
            # Get Round 1 tiebreaker
            r1_key = DataHandler.get_round1_sort_key(round1_dict.get(team_name, {}))
            return (-score, -r2_score, *r1_key)
            
        sorted_data = sorted(data, key=get_sort_key)
        for i, row in enumerate(sorted_data, 1):
            row['Rank'] = str(i)
        return sorted_data

    @staticmethod
    def sort_round4(data: List[Dict[str, Any]], round3_data: List[Dict[str, Any]], 
                    round2_data: List[Dict[str, Any]], round1_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Round 4: Sort by score, then R3, R2, R1 scores"""
        r3_dict = {row['Team Name']: row for row in round3_data}
        r2_dict = {row['Team Name']: row for row in round2_data}
        r1_dict = {row['Team Name']: row for row in round1_data}
        
        def get_sort_key(row):
            team_name = row['Team Name']
            try:
                score = float(str(row.get('Score', '0')).strip() or '0')
                r3_score = float(str(r3_dict.get(team_name, {}).get('Score', '0')).strip() or '0')
                r2_score = float(str(r2_dict.get(team_name, {}).get('Score', '0')).strip() or '0')
            except:
                score, r3_score, r2_score = 0, 0, 0
                
            r1_key = DataHandler.get_round1_sort_key(r1_dict.get(team_name, {}))
            return (-score, -r3_score, -r2_score, *r1_key)
            
        sorted_data = sorted(data, key=get_sort_key)
        for i, row in enumerate(sorted_data, 1):
            row['Rank'] = str(i)
        return sorted_data

    @staticmethod
    def calculate_overall(round_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Calculate and sort overall scores with proper tiebreaking"""
        teams = {}
        
        # Initialize from Round 1 and calculate R1 points
        for team in round_data.get('round1', []):
            team_name = team.get('Team Name', '')
            if team_name:
                r1_points = 10 if 'complete' in str(team.get('Status', '')).lower() else 0
                teams[team_name] = {
                    'Team Name': team_name,
                    'R1': r1_points,
                    'R2': 0, 'R3': 0, 'R4': 0,
                    'Total Score': r1_points
                }
        
        # Add scores from other rounds
        for round_id in ['round2', 'round3', 'round4']:
            for team in round_data.get(round_id, []):
                team_name = team.get('Team Name', '')
                if team_name in teams:
                    try:
                        score = float(str(team.get('Score', '0')).strip() or '0')
                    except:
                        score = 0
                    teams[team_name][f'R{round_id[-1]}'] = score
                    teams[team_name]['Total Score'] += score
        
        # Sort with tiebreaking
        result = list(teams.values())
        result.sort(key=lambda x: (
            -float(x['Total Score']),  # Total score
            -float(x['R4']),          # R4 tiebreaker
            -float(x['R3']),          # R3 tiebreaker
            -float(x['R2']),          # R2 tiebreaker
            -float(x['R1'])           # R1 tiebreaker
        ))
        
        # Add ranks
        for i, row in enumerate(result, 1):
            row['Rank'] = str(i)
            
        return result
