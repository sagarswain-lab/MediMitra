from fastapi import APIRouter
from models.schemas import FeedbackRequest
from database import get_connection
import json

router = APIRouter()

@router.post("/submit")
async def submit_feedback(data: FeedbackRequest):
    """
    Submits user rating and feedback text to the database.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_feedback (rating, feedback, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (data.rating, data.feedback_text))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully! Thank you for your review."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save feedback: {str(e)}"
        }
