# octo
full text file search lan system

1. Octo (сокращ. от octopus) - сетевой поисковик-классификатор. Реализует полнотекстовый поиск внутри документов (doc, docx, odt) на хостах сети с целью последующей автоматической классификации найденных документов. Разработан с целью поиска конфиденциальных документов в корпоративных сетях. Микросервисная архитектура проекта состоит из сетевого поисковика, векторайзера (выделяющего тэги в тексте документов, собранных в базу поисковиком, и строящего векторные представления тэгов) и классификатора, выделяющего категорию текста по косинусной близости векторов тэгов.

    Программа является по сути средством автоматизации утилиты recoll, входящей в базовый пакет многих дистрибутивов Linux.
    Т.к. recoll предварительно индексирует документы на хостах, поиск по всей сети, как правило, занимает не больше минуты.
    Программа позволяет работать с пулом сетей. Результаты поиска скидываются в базу данных, где просмотреть их можно любым удобным sql-браузером, а также сделать экспорт в любом удобном формате.

    Алгоритм работы сделующий:

    #python3 octo.py 

    Octo в несколько потоков обращается к хостам локальной сети по ssh (22 порт), авторизуется на них под локальным админом и выполняет следующие действия на выбор:

        1. Установка octo на хосты

        2. Поиск на хостах

        3. Индексирование хостов

2. Варианты развертывания Octo:

    2.1. Docker - самый простой способ деплоя. В каталоге проекта лежит docker-compose.yaml, перед использованием которого следует указать следующие настройки:
 
    В файле settings/settings.yaml
    
    networks:
    
      - lan: 192.168.0.

        pwd: SecretPWD # пароль локального админа
        
        range: # диапазон хостов сети (с какого по какой сканировать)
          - 2 
          - 254

        usr: admin  # логин локального админа
        
    db_connection:
    
      dbms: postgresql
      
      usr: postgres
      
      pwd: SECRET_PWD
      
      host: localhost
      
      port: 5432
      
      db: postgres
    
    Если сетей несколько, то блок networks будет выглядеть следующим образом:
    
    networks:
      - lan: 192.168.1. # первые три октета первой сети
      
        pwd: SecretPWD # пароль локального админа 1
        
        range: # диапазон хостов сети 1 (с какого по какой сканировать)
          - 2 
          - 254
          
        usr: admin  # логин локального админа 1
        
        - lan: 192.168.2. # первые три октета второй сети
       
        pwd: SecretPWD # пароль локального админа 2
        
        range: # диапазон хостов сети 2 (с какого по какой сканировать)
          - 2 
          - 254
          
        usr: admin  # логин локального админа 2
        
        Docker-compose.yaml описан для автоматического старта контейнеров СУБД Postgres и pgAdmin 


  2.2. Развертывание Octo без использования docker потребует предварительной установки на машину, с которой будет осуществляться сканирование хостов, зависимостей из файла requirements.txt

        Удобная команда для установки при помощи pip: #pip3 install -r requirements.txt

3. Настройки подключения к СУБД:
   
    В блоке db_connection конфигурационного файла settings/settings.yaml укажите свою СУБД и пользователя.
    Т.к. octo использует SQLAlchemy, Вы можете использовать удобную для Вас СУБД. В примере используется Postgres.
    
    Структура БД создается автоматически.
    
4. Настройка octo на хостах
  
    Для того, чтобы утилита Recoll могла смотреть текстовые файлы doc и docx на хосте должна быть установлена утилита 'antiword', пакет 'wv', для odt-документов - 'python-libxslt1'.

    К счастью octo настраивает хосты автоматически. Для того, чтобы настройка прошла успешно, достаточно, чтобы хосты имели доступ к репозитарию ПО и в нем имелись указанные пакеты. Если в репозитарии данные пакеты отсутствуют, то алгоритм экспортирует их на удаленные хосты из каталога packages и установит.

    На удаленный хост из каталога exfiles будут доставлены следующие файлы конфигурации recoll и cron:

      /root/.recoll/recoll.conf

      /var/spool/cron/crontabs/root

      Для запуска настройки хостов для работы с octo выполните: # python3 octo.py install
    
5. Индексирование хостов

    Перед тем как что-либо искать на хостах, требуется проиндексировать локально их содержимое утилитой recoll.
    В планировщике cron каждого хоста добавлено задание на индексацию каждый день в 13.00.
    В случае необходимости ручного запуска индексирования на хостах в сети выполните:
    
    # python3 octo.py index,
    
    или    # python3 octo.py , а затем пункт 4 
    

6. Поиск документов, удовлетворяющих поисковому запросу

    Поиск осуществляется по вхождению ключевого слова в теле каждого документа каждого сетевого хоста. результат помещается в БД. Ищутся все словоформы поискового запроса.

      Для запуска поиска выполните: # python3 octo.py search 'поисковый запрос', или    # python3 octo.py , а затем пункт 2
    
    
  Полезное:
  
    Файл octo.py является инструкциями для Net-helper.py, который в свою очередь предназначен для управления хостами сети. Net-helper может ставить/удалять пакеты на хосты Вашей сети (посредством apt, dpkg), экспортировать с/ импортировать на машину, на которой запущен octo, файлы с/на хосты в сети, а также выполнять произвольные команды (linux bash) на хостах сети.
  
  Перспективы развития:
  
   - написать микросервис тэгинатор-векторайзер для выделения облака тэгов из текстов найденных поисковиком документов с последующим представлеением их в вектор;
   - написать микросервис классификатор на базе сравнения полученных векторов с предварительно подготовленными векторами конфиденциальных документов;
   - написать микросервис ИИ для повторной углубленной перепроверки классификатора.
    
    
