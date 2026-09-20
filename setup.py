from setuptools import find_packages, setup 

setup( 
    name='WSU-SU21-CPTS322-Project', 
    version='0.1', 
    description='', 
    author='', 
    author_email='', 
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'flask-bcrypt',
        'flask-login',
        'markupsafe',
        'pandas',
        'configparser',
        'pyotp',
        'qrcode',
        'xlsxwriter'
    ]
) 