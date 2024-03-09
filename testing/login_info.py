def grab_login(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    if len(lines) != 3:
        raise ValueError("Login information provided incorrectly. Please re-check 'testlogininfo.txt'.")
    return lines[1].strip(), lines[2].strip()