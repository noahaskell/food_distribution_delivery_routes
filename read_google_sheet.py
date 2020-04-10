import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def read_sheet(sheet_id, data_range):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().batchGet(spreadsheetId=sheet_id,
                                     ranges=data_range).execute()
    return result


def make_address_list(gs_list):
    headers = gs_list[0]
    name_idx = headers.index('Name')
    street_idx = headers.index('Street address')
    city_state_idx = headers.index('City, State')
    zip_idx = headers.index('Zip code')
    role_idx = headers.index('Pick-up or Delivery')
    fixed_route_idx = headers.index('Driver')

    add_idx = [street_idx, city_state_idx, zip_idx]
    add_list = []
    driver_idx = []

    for i, v in enumerate(gs_list[1:]):
        this_add_list = []
        if v != []:
            this_add = ', '.join([v[j] for j in add_idx])
            if this_add != ', , ':
                this_add_list.append(v[name_idx].strip())
                this_add_list.append(this_add.strip())
                if len(v) > 6:
                    route_indicator = v[fixed_route_idx]
                else:
                    route_indicator = None
                this_add_list.append(route_indicator)
                if v[role_idx] == 'DRIVER':
                    this_add_list.append(1)
                    driver_idx.append(i)
                else:
                    this_add_list.append(0)
                add_list.append(this_add_list)
    return add_list, driver_idx


if __name__ == '__main__':
    v = read_sheet()

