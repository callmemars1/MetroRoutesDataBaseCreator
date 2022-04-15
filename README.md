# MetroRoutesDataBaseCreator
Simple script for creating or appending existing database from hh api\

Данный скрипт создаёт базу данных, которая содержит в себе все станции указанного метро, а так же все возможные пересечения станций  
```sql
SELECT s1.name, s2.name,n.approximate_time FROM neighboring n
LEFT JOIN stations s1 on s1.id = n.first_station_id_FK
LEFT JOIN stations s2 on s2.id = n.second_station_id_FK
WHERE s1.name = 'Садовая'
```
Данный запрос позволяет получить все станции, на которые можно попасть со станции Садовая, а так же время, которое на это потребуется в секундах  
![image](https://user-images.githubusercontent.com/86615975/163629551-8a3b7c18-48d5-4e82-8edb-c9107dddbc98.png)


Скрипт содержит параметры запуска

'--api_city_id' - id города с hh api (https://github.com/hhru/api/blob/master/docs/metro.md)  
'--db_dir' - Путь к файлу, содержащему базу данных. Если базы данных не существует, то она будет создана согласно этой строке (Обязательно указать имя файла с расширением. Пример пути: D:\Labs\MetroApp\Rsc\MetroDataBase.sqlite)  
'--create_new' - Опциональный аргумент. Если выставить значение True, база данных будет УДАЛЕНА И ПОЛНОСТЬЮ ПЕРЕПИСАНА!!!!! По умолчанию значение false. В таком режиме скрипт дописывает данные в базу  
Пример полной строки запуска:  
--api_city_id 2 --db_dir "C:\Users\Sergey Martynov\DataGripProjects\SQL_TEST\MetroRoutes.sqlite" --create_new True  


