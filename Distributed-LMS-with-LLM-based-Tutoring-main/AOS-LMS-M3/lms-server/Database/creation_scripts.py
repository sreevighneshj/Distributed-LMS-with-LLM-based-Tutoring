import sqlite3

def create_users(cur):
    query = """
    create table if not exists users 
(
    id         uuid,
    username   text,
    password   text,
    email      text,
    phone      text,
    role_id    uuid,
    created_at timestamp,
    primary key (id),
    foreign key (role_id) references roles
);


    """
    cur.execute(query)

def create_roles(cur):
    query = """
    CREATE TABLE IF NOT EXISTS roles (
    id uuid PRIMARY KEY,
    name text
    )
    """
    cur.execute(query)

def create_course_enrolled(cur):
    query = """
    create table if not exists course_enrolled
(
    course_id  uuid,
    user_id    uuid,
    created_at timestamp,
    primary key (course_id, user_id),
    foreign key (course_id) references courses,
    foreign key (user_id) references users
);


    """
    cur.execute(query)

# def create_term(cur):
#     query = """
#     CREATE TABLE IF NOT EXISTS term (
#     id uuid PRIMARY KEY,
#     term_name text,
#     created_at timestamp
#     )
#     """
#     cur.execute(query)

def create_course(cur):
    query = """
    create table if not exists courses
(
    id            uuid,
    course_name   text,
    course_code   text,
    instructor_id uuid,
    created_at    timestamp,
    primary key (id),
    foreign key (instructor_id) references users
);


    """
    cur.execute(query)

def create_assignments(cur):
    query = """
    create table if not exists assignments
(
    id          uuid,
    name        text,
    due_date    timestamp,
    description text,
    course_id   uuid,
    created_at  timestamp,
    primary key (id),
    foreign key (course_id) references courses
);


    """
    cur.execute(query)

def create_assignment_submissions(cur):
    query = """
    create table if not exists assignment_submissions
(
    assignment_id uuid,
    user_id       uuid,
    filename      text,
    created_at    timestamp,
    primary key (assignment_id, user_id),
    foreign key (assignment_id) references assignments,
    foreign key (user_id) references users
);


    """
    cur.execute(query)

def create_materials(cur):
    query = """
    create table if not exists materials
(
    id         uuid,
    name       text,
    course_id  uuid,
    file_name  text,
    created_at timestamp,
    primary key (id),
    foreign key (course_id) references courses
);


    """
    cur.execute(query)

def create_queries(cur):
    query = """
    create table if not exists queries
(
    id         uuid,
    query_text text,
    posted_by  uuid,
    reply_by   uuid,
    created_at timestamp,
    course_id  uuid not null,
    reply      text,
    primary key (id),
    foreign key (posted_by) references users,
    constraint queries___fk_courses
        foreign key (course_id) references courses,
    constraint queries_fk_users
        foreign key (reply_by) references users
);


    """
    cur.execute(query)


def create_node_discovery(cur):
    query = """
    CREATE TABLE IF NOT EXISTS node_discovery (
    id uuid PRIMARY KEY,
    host text,
    port text,
    created_at timestamp,
    is_leader boolean DEFAULT false
    )
    """
    cur.execute(query)


def create_raft_logs(cur):
    query="""
    CREATE TABLE IF NOT EXISTS raft_logs (
    id uuid  PRIMARY KEY,
    operation text,
    args text,
    term integer,
    idx integer,
    commited boolean,
    created_at timestamp
    )
    
    """
    cur.execute(query)
# def create_config(cur):
#     query = """
#     CREATE TABLE IF NOT EXISTS config (
#     id uuid PRIMARY KEY,
#     cur_term uuid,
#     FOREIGN KEY(cur_term) REFERENCES term(id)
#     )
#     """
#     cur.execute(query)
def insert_nodes(cur):
    query = """
    INSERT INTO node_discovery(id,host,port,created_at) VALUES ("becedead-63a4-48a8-a017-e284cd02d21e","localhost","50054","2024-10-22T22:45:00+0530")

    """
    cur.execute(query)
def create_everything():
    try:
        with sqlite3.connect('lms.db') as conn:
            cur = conn.cursor()
            create_roles(cur)
            create_users(cur)
            # create_term(cur)
            create_course(cur)
            create_assignments(cur)
            create_course_enrolled(cur)
            create_assignment_submissions(cur)
            create_materials(cur)
            create_queries(cur)
            create_node_discovery(cur)
            create_raft_logs(cur)
            # insert_nodes(cur)
            # create_config(cur)
    except Exception as e:
        print(e)
        conn.rollback()
    else:
        conn.commit()
        cur.close()

# create_everything()

