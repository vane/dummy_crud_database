dummy crud database
===


#### Description
I always wanted to make simple database so I made one only for educational purposes inspired by this [javaworld article](http://javaworld.com/article/2076333/java-web-development/use-a-randomaccessfile-to-build-a-low-level-database.html)  

It can store any binary data. 
Implemented in python in under 250 lines of code.  
Probably can be shorter but it's just a gig.

Supports
- insert data  
- update data  
- delete data
- read data by index
- read all data

For simplicity data and index files is append only.  
Index file is loaded and stored as dictionary in memory on start.

#### Dependencies
Depends on psutil to display pid statistics when running main file.

#### Run

I tested it using python3.7 but it can be easily converted to any python version or any language  

By default it :
- removes 2 files test.db, test.index if those files exists
- create 2 files test.db, test.index  
- writes and index 100k random string with characters between (100, 1000) to test.db file
- reads 100k random elements from file
- performs read of object at position 2
- remove object from position 3
- update object at position 2

```python
python dummy_crud_database.py 
```

#### Output
```bash
write elements 100000 in 70.1026759147644
read elements 100000 in 3.7399983406066895
size :  100000
database fsize :  53.91 MB
index fsize :  0.76 MB
pid memory usage :  25.61 MB
```

So it looks like it can do 1,4k inserts per second and around 26k reads per second on my computer (write time is including generation of random data).
