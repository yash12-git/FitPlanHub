# Standard Library Imports
from datetime import datetime, timedelta
from typing import Optional, List

# Third Party Imports
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt


DB_CONNECTION = "mysql+pymysql://root:1122yash2211@localhost/FitHub"
JWT_SECRET = "my_super_secure_secret_key_123"
HASH_ALGO = "HS256"
SESSION_DURATION = 60 

try:
    sql_engine = create_engine(DB_CONNECTION)
    SessionManager = sessionmaker(autocommit=False, autoflush=False, bind=sql_engine)
    BaseModelSQL = declarative_base()
except Exception as err:
    print(f"CRITICAL DB ERROR: {err}")

class Member(BaseModelSQL):
    __tablename__ = "app_members"
    member_id = Column(Integer, primary_key=True, index=True)
    handle = Column(String(50), unique=True, index=True)
    contact_email = Column(String(100), unique=True)
    security_hash = Column(String(255))
    account_type = Column(String(20)) 

class Workout(BaseModelSQL):
    __tablename__ = "workouts"
    workout_id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("app_members.member_id"))
    workout_name = Column(String(100))
    details = Column(Text)
    cost = Column(DECIMAL(10, 2))
    program_length = Column(Integer)
    
    creator = relationship("Member")

class Enrollment(BaseModelSQL):
    __tablename__ = "enrollments"
    enroll_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("app_members.member_id"))
    workout_id = Column(Integer, ForeignKey("workouts.workout_id"))

class Connection(BaseModelSQL):
    __tablename__ = "connections"
    fan_id = Column(Integer, ForeignKey("app_members.member_id"), primary_key=True)
    coach_id = Column(Integer, ForeignKey("app_members.member_id"), primary_key=True)

BaseModelSQL.metadata.create_all(bind=sql_engine)

class NewMemberSchema(BaseModel):
    username: str
    password: str
    mode: str 

class NewWorkoutSchema(BaseModel):
    title: str
    info: str
    price: float
    days: int

hasher = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_flow = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_database():
    sess = SessionManager()
    try:
        yield sess
    finally:
        sess.close()

def generate_token(claims: dict):
    payload = claims.copy()
    expiry = datetime.utcnow() + timedelta(minutes=SESSION_DURATION)
    payload.update({"exp": expiry})
    return jwt.encode(payload, JWT_SECRET, algorithm=HASH_ALGO)

def get_active_user(token: str = Depends(oauth2_flow), db: Session = Depends(get_database)):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[HASH_ALGO])
        user_handle = data.get("sub")
        if user_handle is None: raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired")
    
    found_member = db.query(Member).filter(Member.handle == user_handle).first()
    if found_member is None: raise HTTPException(status_code=401)
    return found_member

api = FastAPI(title="FitHub API")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.post("/auth/signup")
def create_account(user_data: NewMemberSchema, db: Session = Depends(get_database)):
    check_user = db.query(Member).filter(Member.handle == user_data.username).first()
    if check_user:
        raise HTTPException(status_code=400, detail="That handle is already taken.")
    
    secure_pw = hasher.hash(user_data.password)

    gen_email = f"{user_data.username}@fithub.local"
    
    new_guy = Member(
        handle=user_data.username,
        contact_email=gen_email,
        security_hash=secure_pw,
        account_type=user_data.mode
    )
    
    try:
        db.add(new_guy)
        db.commit()
    except Exception as e:
        print(f"SIGNUP ERROR: {e}")
        raise HTTPException(status_code=500, detail="Database rejected the entry.")
        
    return {"status": "Account created!"}

@api.post("/auth/login")
def login_user(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_database)):
    member = db.query(Member).filter(Member.handle == form.username).first()
    if not member:
        raise HTTPException(status_code=400, detail="User not found.")
        
    if not hasher.verify(form.password, member.security_hash):
        raise HTTPException(status_code=400, detail="Wrong password.")
    
    token_str = generate_token(claims={"sub": member.handle, "role": member.account_type})
    return {
        "access_token": token_str, 
        "token_type": "bearer", 
        "role": member.account_type, 
        "uid": member.member_id
    }

@api.post("/coach/add-workout")
def publish_workout(plan: NewWorkoutSchema, current: Member = Depends(get_active_user), db: Session = Depends(get_database)):
    if current.account_type != 'coach':
        raise HTTPException(status_code=403, detail="Coaches only area.")
        
    new_wrk = Workout(
        creator_id=current.member_id,
        workout_name=plan.title,
        details=plan.info,
        cost=plan.price,
        program_length=plan.days
    )
    db.add(new_wrk)
    db.commit()
    return {"status": "Workout published"}

@api.get("/coach/my-library")
def get_my_library(current: Member = Depends(get_active_user), db: Session = Depends(get_database)):
    if current.account_type != 'coach': return []
    return db.query(Workout).filter(Workout.creator_id == current.member_id).all()

@api.get("/client/feed")
def get_personal_feed(current: Member = Depends(get_active_user), db: Session = Depends(get_database)):
    my_connections = db.query(Connection.coach_id).filter(Connection.fan_id == current.member_id).all()
    coach_ids = [c[0] for c in my_connections]
    
    my_enrollments = db.query(Enrollment.workout_id).filter(Enrollment.client_id == current.member_id).all()
    bought_ids = [e[0] for e in my_enrollments]

    available_workouts = db.query(Workout).filter(Workout.creator_id.in_(coach_ids)).all()
    
    output = []
    for w in available_workouts:
        is_unlocked = w.workout_id in bought_ids
        output.append({
            "id": w.workout_id,
            "title": w.workout_name,
            "coach": w.creator.handle,
            "price": float(w.cost),
            "days": w.program_length,
            "info": w.details if is_unlocked else "🔒 Locked Content", 
            "unlocked": is_unlocked
        })
    return output

@api.get("/public/coaches")
def list_coaches(current: Member = Depends(get_active_user), db: Session = Depends(get_database)):
    all_coaches = db.query(Member).filter(Member.account_type == 'coach').all()
    
    # Check who I follow
    following_list = db.query(Connection.coach_id).filter(Connection.fan_id == current.member_id).all()
    following_ids = [f[0] for f in following_list]
    
    return [
        {
            "id": c.member_id, 
            "username": c.handle, 
            "is_following": c.member_id in following_ids
        } 
        for c in all_coaches
    ]

@api.post("/actions/enroll/{wid}")
def enroll_in_program(wid: int, current: Member = Depends(get_active_user), db: Session = Depends(get_database)):
    # Check duplicates
    existing = db.query(Enrollment).filter(Enrollment.client_id==current.member_id, Enrollment.workout_id==wid).first()
    if existing: return {"status": "Already enrolled"}
    
    entry = Enrollment(client_id=current.member_id, workout_id=wid)
    db.add(entry)
    db.commit()
    return {"status": "Enrollment successful"}

@api.post("/actions/connect/{cid}")
def toggle_connection(cid: int, current: Member = Depends(get_active_user), db: Session = Depends(get_database)):
    link = db.query(Connection).filter(Connection.fan_id==current.member_id, Connection.coach_id==cid).first()
    if link:
        db.delete(link)
        msg = "Disconnected"
    else:
        new_link = Connection(fan_id=current.member_id, coach_id=cid)
        db.add(new_link)
        msg = "Connected"
    db.commit()
    return {"status": msg}