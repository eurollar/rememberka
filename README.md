Описание приложения
Приложение-календарь Rememberka предназначено для записи пользовательских событий и уведомлениях о приближающихся событиях. Также приложение показывает государственные празники страны, указанной при регистрации пользователя.
Rememberka поддерживает:
1) Регистрация пользователя с указанием страны;
2) Присылание письма на email с уведомлением о регистрации, где указан логин и пароль для авторизации в приложении;
3) Авторизация пользователя в приложении; 
3) Создание пользовательского события;
4) Редактирование пользовательского события;
5) Удаление пользовательского события;
6) Присылания письма на email с уведомлением о грядущем событии;
7) Показ всех событий пользователя;
8) Показ событий за определенный день или месяц;
9) Показ государственных праздников страны, указанной пользователем при регистрации.
Для доступа к данным пользователя необходимо авторизоваться и присылать токен пользователя в заголовке для каждого запроса (кроме создания нового пользователя).

Регистрация пользователя
Регистрация пользователя происходит по endpoint "register/". При регистрации пользователя необходимо указывать логин, email, пароль и страну. Данные поля обязательны к заполнению. После регистрации все данные пользователя сохраняются в базу данных и присылается уведомление на email, указанный при регистрации. В письме содержится логин, пароль и email пользователя.
После создания пользователя, для него получается список всех праздников страны, указанной при регистрации. Список праздников получается с ресурса https://www.officeholidays.com/countries/index.php. Для парсинга праздников конкретной страны используется ссылка https://www.officeholidays.com/ics/ics_country.php?tbl_country=<country_name>, где <country_name> страна пользователя. Сервис отвечает в формате  ics, все праздники сохраняются в базу данных. Осуществляется периодическое обновление праздников всех зарегистрированных пользователей раз в полгода (1 июня).

Авторизация пользователя
Для авторизации пользователя можно использовать как логин, так и email указанные при регистрации. Авторизация пользователя реализована с помощью библиотеки "dj-rest-auth" и авторизации DRF "api-auth".
Endpoints:
1) dj-rest-auth/password/reset/ - указывается email для сброса текущего пароля;
2) dj-rest-auth/password/reset/confirm/ - указывается uid, token и новый пароль после сброса; Uid и token присылаются на указанную почту в endpoint "dj-rest-auth/password/reset/";
3) dj-rest-auth/login/ - указыватся username или email, пароль для аутентификации. Возвращает токен;
4) dj-rest-auth/logout/ - выход из текущей аутентификации пользователя;
5) dj-rest-auth/user/ - показывает информацию о текущем пользователе. Здесь можно редактировать данные о текущем пользователе;
6) dj-rest-auth/password/change/ - изменение пароля текущего пользователя.

Получение всех событий для пользователя
Показ всех событий пользователя происходит по endpoint "all-api-data" (GET-запрос).

Добавление пользовательского события
Добавление пользовательских событий происходит по endpoint "add-api-data/" (POST-запрос). Для создания необходимо заполнить поля "title", "start_date", "start_time", "memento" (являются обязательными) и "end_date", "end_time" (являются необязательными).
Описание полей:
1) title - указывается название события, является обязательным к заполнению;
2) start_date - указывается дата начала события в формате "YYYY-MM-DD", является обязательным к заполнению;
3) start_time - указывается время начала события в формате "HH:MM:SS", является обязательным к заполнению;
4) end_date - указывается дата окончания события в формате "YYYY-MM-DD", необязательное поле. Если поле не заполняется, дата устанавливается равной start_date;
5) end_time - указывается время окончания события в формате "HH:MM:SS", необязательное поле. Если поле не заполняется, время устанавливается равной "23:59:59";
6) memento - устанавливается время для напоминания до начала события. По стандарту установлены напоминания "За час", "За 2 часа", "За 4 часа", "За день", "За 3 дня", "За неделю" и эти значения может выбрать пользователь.
7) Поле user заполняется автоматически текущим пользователем и его редактировать нельзя.
После создания события будет приходить письмо на email с упоминанием о начале события за время, которое было указано пользователем в поле "memento".

Просмотр, редактирование, удаление конкретного события (CRUD)
Для просмотра, редактирования или удаления конкретного события используется endpoint "update-api-date/<pk>/", где <pk> является id события. Id указывается в информации о всех событиях.
Поля "title", "start_date", "start_time", "memento" нельзя оставлять пустыми, в остальном, поля заполняются как и для endpoint "add-api-data/".

Получение событий за день
Для получения событий за конкретный день используется endpoint "get-for-day/" (POST-запрос). Здесь необходимо заполнить поле "start_date" в формате "YYYY-MM-DD". Endpoint отдает список событий за выбранный день для текущего пользователя.

Получение событий за месяц
Для получения событий за конкретный месяц используется endpoint "get-for-month/" (POST-запрос). Здесь необходимо заполнить поле "month" натуральным числом, больше нуля и меньше 13. Endpoint отдает список событий за выбранный месяц для текущего пользователя.

Получение всех государственных праздников
Для получения всех государственных праздников для страны пользователя используется endpoint "get-holidays/" (GET-запрос).

Стек
В приложении используется следующий стек:
1) Django REST-framework (DRF);
2) dj-rest-auth;
3) PostreSQL;
4) Celery;
5) Celery-beat schedule;
6) Redis;
7) Requests;
8) Ics;
9) Docker.
Бэкенд реализован с помощью DRF, с базой данных PostreSQL. Отправка email после регистрации и уведомлений, парсинг (с помощью библиотеки requests и ics) праздников осуществяется с помощью Celery с подключенной базой данных Redis. Периодическое обновление государственных праздников всех пользователей осуществялется с помощью Celery-beat schedule. Запуск сервера осуществляет Docker.

Запуск
Для запуска проекта на localhost необходимо установить Docker, зайти в папку проекта, где лежит файл "docker-compose" и запустить в консоли командами "docker-compose build", а затем "docker-compose up". Для запуска тестов необходимо запустить сервер, открыть новую консоль, перейти в папку проекта, где есть файл "docker-compose" и запустить командой в консоли "docker exec -it <namedockercontainer> python3 manage.py test", где <namedockercontainer> - имя контейнера Dokcer (можно узнать в консоли командой "docker ps", найти в столбце "IMAGE" "planner_web" и посмотреть столбец "NAMES" - это и есть имя контейнера Docker).
Для создания суперпользователя необходимо выполнить команду в консоли "docker exec -it <namedockercontainer> python3 manage.py createsuperuser". Затем ввести имя, пароль и email для суперпользователя.
Отправка email происходит через smtp Google. Необходимо в файле проекта "settings.py" отредактировать строчки (номера 171 и 172) "EMAIL_HOST_USER = <youremail>" и "EMAIL_HOST_PASSWORD = <yourpassword>", где <youremail> - Ваша почта gmail, <yourpassword> - пароль от почты. Также, необходимо отредактировать почту в файле "tasks.py", функции "send_reg_mail" и "send_remind". В строчках 17 и 32 необходимо вписать свою gmail почту, вместо 'yourgmail'.
В настройках почты Google для отправки писем, необходимо включить IMAP-доступ.
Открытие IMAP-доступа:
1) Откройте Gmail в браузере;
2) В правом верхнем углу нажмите на значок "Настройки" > "Настройки" > "Все настройки"$;
3) Откройте вкладку Пересылка и POP/IMAP;
4) В разделе "Доступ по протоколу IMAP" выберите "Включить IMAP".
Настройки для баз данных используется файл db_keys.txt. Там можно прописать свои доступы, а именно:
1) Название ДБ (поле "POSTGRES_DB", по умолчанию django_db);
2) Пользователь ДБ (поле "POSTGRES_USER", по умолчанию user);
3) Пароль от ДБ (поле "POSTGRES_PASSWORD", по умолчанию useruser).
Во время запуска проекта в модель базы данных "Remind" по умолчанию создаются следующие значения для выбора времени для упоминания о событии через email:
1) За час;
2) За 2 часа;
3) За 4 часа;
4) За день;
5) За 3 дня;
6) За неделю.
В файле "utils.py" есть функция "convert_date", которая вычисляет время для отправки письма с уведомлением. Для добавления своих значений необходимо также написать в функции вычисления для новых значений. Все значения по умолчанию загружаются из файла json в папке "fixtures". Туда можно добавить собственные значения, отредактировать или удалить имеющиеся в формате json.

Application description.
The Rememberka calendar app is designed to record user events and notify you of upcoming events. The application also displays the national holidays of the country indicated during the user's registration.
Rememberka supports:
1) Registering the user with the country specified;
2) Sending an email notification of registration with a login and password to authorize in the application;
3) Authorizing the user in the application; 
3) Creating a custom event;
4) Editing a custom event;
5) Deleting a custom event;
6) Sending email notification of an upcoming event;
7) Show all user's events;
8) Showing events for a particular day or month;
9) Showing public holidays of the country, specified by the user during registration.
To access user data, you must be logged in and send a user token in the header of each request (except for creating a new user).

User registration
The user is registered at the endpoint "register/". When registering a user it is necessary to specify login, email, password and country. These fields are mandatory. After registration, all user data are saved in the database and a notification is sent to the email specified during registration. The email contains the username, password and email of the user.
After creating the user, a list of all holidays of the country, specified at registration, is obtained for him. The list of holidays is received from the resource https://www.officeholidays.com/countries/index.php. To parse the holidays of a particular country uses the link https://www.officeholidays.com/ics/ics_country.php?tbl_country=<country_name>, where <country_name> is the user's country. Service responds in ics format, all the holidays are stored in the database. There is a periodic update of the holidays of all registered users once every six months (June 1).

User authorization
For user authorization you can use both login and email, indicated during registration. User authorization is implemented with the help of the library "dj-rest-auth" and DRF authorization "api-auth".
Endpoints:
1) dj-rest-auth/password/reset/ - the email for resetting the current password is specified;
2) dj-rest-auth/password/reset/confirm/ - uid, token and new password after resetting; Uid and token are sent to specified email in endpoint "dj-rest-auth/password/reset/";
3) dj-rest-auth/login/ - Specifies username or email, password for authentication. Returns the token;
4) dj-rest-auth/logout/ - exits current user authentication;
5) dj-rest-auth/user/ - shows information about current user. Here you can edit information about the current user;
6) dj-rest-auth/password/change/ - changes the password of current user.

Getting all events for user
All user events are displayed by endpoint "all-api-data" (GET-request).

Adding custom event
Adding of custom events is done by endpoint "add-api-data/" (POST-request). The fields "title", "start_date", "start_time", "memento" (are mandatory) and "end_date", "end_time" (are optional) must be filled to create.
Field description:
1) title - specifies the name of the event, is mandatory;
2) start_date - specifies the start date of the event in the format "YYYYY-MM-DD", which is mandatory;
3) start_time - the time of event start in format "HH:MM:SS", is mandatory;
4) end_date - specifies the date of event end in the format "YYYY-MM-DD", it is optional field. If the field is not filled, the date is set equal to start_date;
5) end_time - the event end time in the format "HH:MM:SS", optional field. If the field is not filled, the time is set equal to "23:59:59";
6) memento - set the time for reminder before the event starts. The standard reminder is set "In an hour", "In 2 hours", "In 4 hours", "In a day", "In 3 days", "In a week" and these values can be chosen by the user.
7) User field is filled automatically by the current user and cannot be edited.
After the event is created, an email will be sent mentioning the start of the event for the time that was specified by the user in the "memento" field.

Viewing, editing, deleting a specific event (CRUD)
The endpoint "update-api-date/<pk>/" is used to view, edit or delete a specific event, where <pk> is the event id. The id is specified in the information about all events.
The fields "title", "start_date", "start_time", "memento" cannot be left blank, otherwise, the fields are filled as for endpoint "add-api-data/".

Get-for-day events
To get events for a specific day, the endpoint "get-for-day/" (POST request) is used. Here you need to fill in the field "start_date" in the format "YYYYY-MM-DD". Endpoint returns a list of events for the selected day for the current user.

Retrieving events for a month
To fetch events for a specific month, the endpoint "get-for-month/" (POST request) is used. Here you need to fill the field "month" with a natural number greater than zero and less than 13. Endpoint returns a list of events for the selected month for the current user.

Retrieving all public holidays
To retrieve all public holidays for the user's country the endpoint "get-holidays/" (GET request) is used.

Stack
The application uses the following stack:
1) Django REST-framework (DRF);
2) dj-rest-auth;
3) PostreSQL;
4) Celery;
5) Celery-beat schedule;
6) Redis;
7) Requests;
8) Ics;
9) Docker.
The backend is implemented using DRF, with a PostreSQL database. Sending email after registration and notifications, parsing (using requests and ics library) of holidays is implemented using Celery with connected Redis database. Periodic updating of public holidays for all users is done with Celery-beat schedule. The server is run by Docker.

Running
In order to start the project on localhost you need to install Docker, go to the project folder where the file "docker-compose" is and run in the console with the commands "docker-compose build" and then "docker-compose up". To run tests, start the server, open a new console, go to the project folder where the file "docker-compose" is and run the command "docker exec -it <namedockercontainer> python3 manage.py test" in the console, where <namedockercontainer> is the name of the Docker container (can be found in the console by command "docker ps", find "planner_web" in the "IMAGE" column and see the "NAMES" column - that is the Docker container name).
To create a superuser, run the command in the console "docker exec -it <namedockercontainer> python3 manage.py createsuperuser". Then enter the name, password, and email for the superuser.
Sending the email is done via Google smtp. It is necessary to edit lines (numbers 171 and 172) "EMAIL_HOST_USER = <youremail>" and "EMAIL_HOST_PASSWORD = <yourpassword>" in file "settings.py" where <youremail> - your mail gmail, <yourpassword> - password from mail. Also, you need to edit the mail in the "tasks.py" file, the functions "send_reg_mail" and "send_remind". In lines 17 and 32 you have to write your gmail instead of 'yourgmail'.
In your Google mail settings, you need to enable IMAP access to send emails.
Opening IMAP access:
1) Open Gmail in your browser;
2) In the upper right corner, click the Settings icon > Settings > All Settings $;
3) Open the Forwarding and POP/IMAP tab;
4) Under "IMAP Access" select "Enable IMAP".
The settings for the databases use the db_keys.txt file. There you can prescribe your accesses, viz:
1) DB name (field "POSTGRES_DB", by default django_db);
2) The user of the db (the field "POSTGRES_USER", by default user);
3) DB password (field "POSTGRES_PASSWORD", useruser by default).
The following values are created in the "Remind" database model during the startup of the project by default to select the time for mentioning the event via email:
1) In one hour;
2) In 2 hours;
3) In 4 hours;
4) Per day;
5) In 3 days;
6) per week.
In the file "utils.py" there is a function "convert_date", which calculates the time to send the notification letter. To add your own values, you must also write in the function calculations for new values. All default values are loaded from the json file in the "fixtures" folder. You can add your own values there, edit or delete existing values in json format.
