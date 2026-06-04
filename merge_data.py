from datetime import datetime, timedelta
import json
import os
import sys


def merge_train_data(input_folder="data/", output_file_pattern="merged_train_data_{}.json", target_date="0528"):
    """
    Merges train data files based on a target date.
    - Captures data_{target_date}*.json EXCEPT data_{target_date}00*.json
    - Captures data_{next_day}00*.json
    Deletes source files upon successful generation.
    """
    merged_data = {}

    # 1. Parse target date and safely calculate next day using datetime (handles month/year crossovers)
    try:
        # Assumes current year context to parse MMDD correctly
        current_year = datetime.now().year
        target_dt = datetime.strptime(f"{current_year}{target_date}", "%Y%m%d")
        next_dt = target_dt + timedelta(days=1)
        next_day_str = next_dt.strftime("%m%d")
    except ValueError:
        print("Error: target_date must be in MMDD format (e.g., '0528')")
        return

    # 2. Filter files manually using os.listdir
    try:
        all_files = os.listdir(input_folder)
    except FileNotFoundError:
        print(f"Error: The folder '{input_folder}' does not exist.")
        return

    file_list = []
    for f in all_files:
        if not f.endswith(".json"):
            continue
            
        # Condition 1: data MMDD but NOT data MMDD 00
        if f.startswith(f"data_{target_date}") and not f.startswith(f"data_{target_date}00"):
            file_list.append(os.path.join(input_folder, f))
            
        # Condition 2: Next day early morning files (data MMDD 00)
        elif f.startswith(f"data_{next_day_str}00"):
            file_list.append(os.path.join(input_folder, f))

    file_list = sorted(file_list)

    if not file_list:
        print(f"No matching source files found for date '{target_date}' in '{input_folder}'.")
        return

    print(f"Found {len(file_list)} files to process...")

    # 3. Processing loop
    for file_path in file_list:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                live_boards = data.get("TrainLiveBoards", [])

                for board in live_boards:
                    train_no = board.get("TrainNo")
                    if not train_no:
                        continue

                    if train_no not in merged_data:
                        merged_data[train_no] = {
                            "No": train_no,
                            "Type": board.get("TrainTypeID"),
                            "Code": board.get("TrainTypeCode"),
                            "Name": board.get("TrainTypeName").get("Zh_tw") if board.get("TrainTypeName") else None,
                            "data": [],
                        }

                    snapshot = {
                        "StationID": board.get("StationID"),
                        "Status": board.get("TrainStationStatus"),
                        "Delay": board.get("DelayTime"),
                        "Update": str(board.get("UpdateTime"))[11:-6],
                    }

                    merged_data[train_no]["data"].append(snapshot)

        except (json.JSONDecodeError, IOError) as e:
            print(f"Skipping error-prone file {file_path}: {e}")

    final_output = [merged_data[tn] for tn in sorted(merged_data.keys())]
    output_file = output_file_pattern.format(target_date)

    # 4. Save results
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_output, f, ensure_ascii=False, separators=(',', ':'))
        print(f"Successfully merged data into {output_file}")
    except IOError as e:
        print(f"Failed to write output file: {e}")
        return

    # 5. Delete source files safely ONLY AFTER output file was created successfully
    print("Cleaning up processed source files...")
    for file_path in file_list:
        try:
            os.remove(file_path)
            print(f"Deleted source file: {file_path}")
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")


if __name__ == "__main__":
    # If a date argument is provided, use it. Otherwise, default to 2 days ago.
    if len(sys.argv) > 1 and sys.argv[1].strip():
        user_date = sys.argv[1].strip()
        print(f"Using manual target date: {user_date}")
    else:
        two_days_ago = datetime.now() - timedelta(days=2)
        user_date = two_days_ago.strftime("%m%d")
        print(f"No date provided. Defaulting to 2 days ago: {user_date}")
    
    merge_train_data(
        input_folder="data/", 
        output_file_pattern="merged_train_data_{}.json", 
        target_date=user_date
    )