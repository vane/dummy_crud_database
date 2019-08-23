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
Optional psutil to display pid statistics when running main file.

#### Run

I tested it using python3.7 but it can be easily converted to any python version or any language  

By default it :
- removes 2 files test.db, test.index if those files exists
- create 2 files test.db, test.index  
- writes and index 1 million random string with characters between (100, 1000) to test.db file (around 540MB)
- reads 1 million random elements from file (around 8MB)
- performs read of object at position 2
- remove object from position 3
- update object at position 2

```python
python dummy_crud_database.py 
```

#### Output
```bash
Test elements size 1000000
write elements in 35.61809206008911s - 28075.61950013945 per second
read elements in 13.677339792251587s - 73113.63285472477 per second
size :  1000000
database fsize :  539.06 MB
index fsize :  7.63 MB
```


So it looks like it can do 1,4k inserts per second and around 26k reads per second on my computer (write time including random choice from 1k elements array).
