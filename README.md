# Acme Food Bank Inventory Tracking System
WSU-SU21-CPTS322-Project



## Project summary

### Description of the project
A web application for efficient inventory management of food and hygiene product donations using Python, Flask, HTML, JavaScript and SQLite.

### Additional information about the project
The Acme Food Bank Inventory Tracking System is designed to address the challenges faced by food banks in managing frequent and varied donations. This system aims to facilitate real-time updates, provide secure user authentication, and generate detailed reports to enhance operational efficiency. It offers a user-friendly interface for managing inventory, tracking donations, updating stock, and processing recipient orders.

## Installation

### Prerequisites

Before you begin, ensure you have the following installed on your machine:
- Git
- Python (version 3.8 or higher)
- SQLite
- SQLAlchemy

### Installation Steps

#### Setup
Before development, creating a virtual environment is recommended.
To create a virtual environment, run:
````
python -m venv venv
````
then activate it on windows with:
````
.\venv\Scripts\Activate.ps1
````
or on linux by running:
````
source ./venv/bin/activate
````

Then, install all dependencies with:
````
pip install -e .
````
#### Running

To run the **development server**, enter the src directory (``cd src``) and run:
````
python app.py
````

### Accessing on other devices

If connecting to the server's IP address doesn't work on other devices and the server is using Windows, make sure to set the Wifi network to a private network and then disable Microsoft Defender Firewall.

## Using TLS Encryption

To configure the server to use HTTPS, ``SSL_Enabled`` must be set to ``True`` in ``server.ini``.

Without manually set certificates, the server will use a temporary "ad-hoc" certificate. This will cause the browser to give a warning (which can be dismissed in Chrome by clicking ``Advanced -> Proceed to [address] (unsafe)`` or in Firefox with ``Advanced -> Add Exception``). Keep in mind that this will still create a secure, encrypted connection.

To circumvent this, you can
- Create a self signed certificate using openSSL, import it in the user's browser.
- Use a service like LetsEncrypt to generate a certificate for your server.

Then put your certificates in the ``src/certs/`` folder and add their filenames in ``server.ini`` under ``Server_Certificate`` and ``Server_Key``

## 2-Factor Authentication

To enable 2FA, go to your user account page and click "Set up 2-Factor Authentication" and follow the steps provided. Right now, 2FA can't be disabled for the user, but the setup page can be revisited in case you need to connect a new authenticator or lost access to the secret token.

## Functionality

To use the Acme Food Bank Inventory Tracking System, follow these steps:

1. **Log In/Sign Up**: Users can sign up for a new account or log in to an existing one.
2. **Homepage**: Upon logging in, users are taken to the dashboard which provides an overview of general information.
3. **Add New Donation**: Navigate to the "Add Donation" page to enter details of new donations and update the inventory.
4. **Update Inventory**: Modify existing inventory items by navigating to the "Update Inventory" page.
5. **Generate Report**: Create customized reports by selecting the desired parameters on the "Generate Report" page.
7. **Recipient Orders**: Recipients can place their demand requests, which are processed by the system.
8. **User Center**: Users can costumize their avatar and change their username, email address and password.


## Known Problems

For an up-to-date list of known issues, please refer to the [GitHub Issues Board](https://github.com/YaruG1022/WSU-SU21-CPTS322-Project/issues). 
If you encounter a new issue, please open a new issue on our GitHub Issues Board, providing as much detail as possible to help us diagnose and fix the problem.

## Contributing
We welcome contributions from the community! Follow these steps to contribute:

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## Additional Documentation

For more detailed documentation, refer to the following files:
- [Sprint Reports](Sprint_Reports)

## License
This project is licensed under the MIT License. See the [LICENSE.txt](LICENSE.txt) file for details.
