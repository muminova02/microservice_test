from fastapi import FastAPI, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
import os

app = FastAPI(title="Target Service", description="Target Management Service")

# Models (in a real app, this would be in separate files)
class TargetBase(BaseModel):
    title: str
    description: str
    deadline: str
    completed: bool = False

class TargetCreate(TargetBase):
    pass

class Target(TargetBase):
    id: int
    user_id: str

    class Config:
        from_attributes = True

# Mock database (would use real database in production)
targets_db = [
    {
        "id": 1,
        "title": "Complete Python microservice",
        "description": "Finish the FastAPI target service",
        "deadline": "2025-08-01",
        "completed": False,
        "user_id": "johndoe"
    },
    {
        "id": 2,
        "title": "Learn Kubernetes",
        "description": "Study Kubernetes for deploying microservices",
        "deadline": "2025-09-01",
        "completed": False,
        "user_id": "johndoe"
    }
]

# Endpoints
@app.get("/targets", response_model=List[Target])
async def get_all_targets():
    return targets_db

@app.get("/targets/{target_id}", response_model=Target)
async def get_target(target_id: int):
    for target in targets_db:
        if target["id"] == target_id:
            return target
    raise HTTPException(status_code=404, detail="Target not found")

@app.get("/targets/user/{user_id}", response_model=List[Target])
async def get_user_targets(user_id: str):
    user_targets = [target for target in targets_db if target["user_id"] == user_id]
    return user_targets

@app.post("/targets", response_model=Target, status_code=status.HTTP_201_CREATED)
async def create_target(target: TargetCreate, user_id: str):
    # In real app, get user_id from token
    new_id = max([t["id"] for t in targets_db]) + 1 if targets_db else 1
    new_target = {
        "id": new_id,
        **target.dict(),
        "user_id": user_id
    }
    targets_db.append(new_target)

    # In real app, publish event to RabbitMQ
    # publish_message("target_created", new_target)

    return new_target

@app.put("/targets/{target_id}", response_model=Target)
async def update_target(target_id: int, target: TargetCreate, user_id: str):
    for i, existing_target in enumerate(targets_db):
        if existing_target["id"] == target_id:
            if existing_target["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to update this target")

            targets_db[i] = {
                "id": target_id,
                **target.dict(),
                "user_id": user_id
            }
            return targets_db[i]
    raise HTTPException(status_code=404, detail="Target not found")

@app.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(target_id: int, user_id: str):
    for i, target in enumerate(targets_db):
        if target["id"] == target_id:
            if target["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to delete this target")

            targets_db.pop(i)
            return
    raise HTTPException(status_code=404, detail="Target not found")

@app.patch("/targets/{target_id}/complete", response_model=Target)
async def complete_target(target_id: int, user_id: str):
    for i, target in enumerate(targets_db):
        if target["id"] == target_id:
            if target["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to update this target")

            targets_db[i]["completed"] = True
            # In real app, publish event to RabbitMQ for notification
            # publish_message("target_completed", targets_db[i])
            return targets_db[i]
    raise HTTPException(status_code=404, detail="Target not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
