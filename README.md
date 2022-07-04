# octo
full text file search lan system

1. Octo (сокращ. от octopus) - сетевой поисковик. Реализует полнотекстовый поиск внутри документов (doc, docx, odt) на хостах сети с целью последующей автоматической классификации найденных документов. Разработан с целью поиска конфиденциальных документов в корпоративных сетях. Микросервисная архитектура проекта состоит из сетевого поисковика, векторайзера (выделяющего тэги в тексте документов, собранных в базу поисковиком, и строящего векторные представления тэгов) и классификатора, выделяющего категорию текста по косинусной близости векторов тэгов.

    Программа является по сути средством автоматизации утилиты recoll, входящей в базовый пакет многих дистрибутивов Linux.
    Т.к. recoll предварительно индексирует документы на хостах, поиск по всей сети, как правило, занимает не больше минуты.
    Программа позволяет работать с пулом сетей. Результаты поиска скидываются в базу данных, где просмотреть их можно любым удобным sql-браузером, а также сделать экспорт в любом удобном формате.

    Алгоритм работы сделующий:

        #python3 octo.py

    Octo в несколько потоков обращается к хостам локальной сети по ssh (22 порт), авторизуется на них под локальным админом и выполняет следующие действия на выбор:

        1. Установка octo на хосты

        2. Поиск на хостах

        3. Индексирование хостов

   1. Варианты развертывания Octo:
      1. Docker Compose - самый простой способ деплоя. В каталоге проекта лежит docker-compose.yaml, перед использованием которого следует указать настройки сканируемых сетей в конфигурационном файле /settings/settings.yaml.

      Пример запуска контейнера для поиска документов, содержащих фразу "hello world!", на хостах в сети:
      docker run --name octo --rm --network=host -e 'OCTO_MODE=search' -e 'OCTO_REQUEST=hello world!' -v octo:/usr/src/octo/settings octo

      2. Развертывание Octo без использования docker потребует предварительной установки на машину, с которой будет осуществляться сканирование хостов, зависимостей из файла requirements.txt

             #pip3 install -r requirements.txt

2. Настройки подключения к СУБД:

    В блоке db_connection конфигурационного файла settings/settings.yaml укажите свою СУБД и пользователя.
    Т.к. octo использует SQLAlchemy, Вы можете использовать удобную для Вас СУБД. В примере используется Postgres.

    Структура БД создается автоматически.

3. Настройка octo на хостах

    Для того, чтобы утилита Recoll могла смотреть текстовые файлы doc и docx на хосте должна быть установлена утилита 'antiword', пакет 'wv', для odt-документов - 'python-libxslt1'.

    К счастью octo настраивает хосты автоматически. Для того, чтобы настройка прошла успешно, достаточно, чтобы хосты имели доступ к репозитарию ПО и в нем имелись указанные пакеты. Если в репозитарии данные пакеты отсутствуют, то алгоритм экспортирует их на удаленные хосты из каталога /packages и установит.

    На удаленный хост из каталога exfiles будут доставлены следующие файлы конфигурации recoll и cron:

          /root/.recoll/recoll.conf

          /var/spool/cron/crontabs/root

      Для запуска настройки хостов для работы с octo выполните: # python3 octo.py install

4. Индексирование хостов

    Перед тем как что-либо искать на хостах, требуется проиндексировать локально их содержимое утилитой recoll.
    В планировщике cron каждого хоста добавлено задание на индексацию каждый день в 13.00.
    В случае необходимости ручного запуска индексирования на хостах в сети выполните:

    **# python3 octo.py index,**

    или    # python3 octo.py , а затем пункт 4


6. Поиск документов, удовлетворяющих поисковому запросу

    Поиск осуществляется по вхождению ключевого слова в теле каждого документа каждого сетевого хоста. результат помещается в БД. Ищутся все словоформы поискового запроса.

      Для запуска поиска выполните: # python3 octo.py search 'поисковый запрос', или    # python3 octo.py , а затем пункт 2


  Перспективы развития:

   - оптимизация микросервиса тэгинатор-векторайзер для выделения облака тэгов из текстов найденных поисковиком документов с последующим представлеением их в вектор;
   - оптимизация микросервиса классификации;
   - реализовать прототип микросервиса ИИ для повторной углубленной перепроверки классификатора.


