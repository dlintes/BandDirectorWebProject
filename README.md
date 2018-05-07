# BandDirectorWebProject
Web project that holds a platform of communication between director and student
Steps to install the project:
          • 	Copy the WebProject folder to your desired location
          •	Install virtual environment or you can use an already existing Python installation.
          •	Install all the required modules by running: 
            pip install -r WebProject/WebProject/requirements.txt  (assuming the root folder is WebProject)
          •	Install MySQL 5.7.21 or later. If you have MySQL already installed just use the info in config.py to change connectivity string             to point to existing MySQL installation,
          •	Set it up to run on port 4300 . 
                 o	The port is configurable in config.py file if needed to be changed. 
                 o	Password to connect to MySQL instance is also configurable in config.py. Search for the following variable in config.py                     and change it accordingly:SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or       
                    \"mysql+pymysql://root:root@localhost:3306/web"
          •	Install MySQL workbench as the MySQL client that would allow the user to connect to the database and run queries.
          •	Source WebProject\db\empty_db.sql in order to create all the MySQL schemas and objects 
          •	To start the web app run  <PATH>WebProject\WebProject\manage.py runserver 
