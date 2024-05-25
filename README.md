Инструкци по запуску:  
Создайте файл .env и внесите туда следующие переменные:  
  PG_HOST=postgres  
  PG_PORT=5432  
  PG_USER=username  
  PG_PASSWORD=userpassword  
  PG_DBNAME=userpg  
  FOOTBAll_KEY= получите ключ на сайте https://www.api-football.com/  
  SECRET_KEY= сгенерируйте любой uuid  
  FLASK_PORT=5000  

Первый запуск: docker compose up -d --build  
Остановка: docker compose stop  
Запуск: docker compose up -d  

Ссылки для postman:  
  #get  
  Получить данные команд, лиг, игроков, стадионов: http://127.0.0.1:5000/models, models = teams, players, stadiums, leagues.  
  #post  
  Созать запись команды, лиги, игрока, команды: http://127.0.0.1:5000/model/create  
  #put  
  Обновить запись: http://127.0.0.1:5000/model/update  
  #delete  
  Удалить запись: http://127.0.0.1:5000/model/delete  
  #model = team, player, stadium, league  
