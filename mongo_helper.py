# mongo_helper.py
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

class MongoHelper:
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/solemn_declarations')
        self.client: Optional[MongoClient] = None
        self.db = None
        self.mongo_available = False
        self._connect()
    
    def _connect(self):
        """Initialize MongoDB connection with fallback"""
        try:
            self.client = MongoClient(
                self.mongo_url,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            # Test connection
            self.client.admin.command('ping')
            
            # Get database name from URL or use default
            db_name = self.mongo_url.split('/')[-1] if '/' in self.mongo_url else 'solemn_declarations'
            self.db = self.client[db_name]
            
            self.mongo_available = True
            print("MongoDB connected successfully")
            
            # Create indexes for better performance
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"MongoDB connection failed: {e}. Falling back to JSON file storage.")
            self.mongo_available = False
        except Exception as e:
            print(f"MongoDB setup error: {e}. Falling back to JSON file storage.")
            self.mongo_available = False
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        if not self.is_available():
            return
        
        try:
            # Submissions collection indexes
            submissions = self.db.submissions
            submissions.create_index("submission_id", unique=True)
            submissions.create_index("email")
            submissions.create_index("created_at")
            submissions.create_index([("email", 1), ("created_at", -1)])
            
            # Metrics collection indexes
            metrics = self.db.metrics
            metrics.create_index([("metric_name", 1), ("timestamp", -1)])
            metrics.create_index("date")
            
            print("MongoDB indexes created successfully")
        except Exception as e:
            print(f"Warning: Could not create MongoDB indexes: {e}")
    
    def is_available(self) -> bool:
        """Check if MongoDB is available"""
        return self.mongo_available and self.client is not None and self.db is not None
    
    def save_submission(self, submission_data: Dict[str, Any]) -> bool:
        """Save form submission to MongoDB"""
        if not self.is_available():
            return False
        
        try:
            # Add metadata
            submission_data.update({
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'status': 'submitted',
                'email_verified': True  # Since OTP was verified
            })
            
            result = self.db.submissions.insert_one(submission_data)
            return result.acknowledged
        except Exception as e:
            print(f"Error saving submission to MongoDB: {e}")
            return False
    
    def get_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Get submission by ID"""
        if not self.is_available():
            return None
        
        try:
            submission = self.db.submissions.find_one(
                {"submission_id": submission_id},
                {"_id": 0}  # Exclude MongoDB ObjectId
            )
            return submission
        except Exception as e:
            print(f"Error fetching submission from MongoDB: {e}")
            return None
    
    def get_submissions_by_email(self, email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get submissions by email address"""
        if not self.is_available():
            return []
        
        try:
            cursor = self.db.submissions.find(
                {"email": email},
                {"_id": 0}  # Exclude MongoDB ObjectId
            ).sort("created_at", -1).limit(limit)
            
            return list(cursor)
        except Exception as e:
            print(f"Error fetching submissions by email from MongoDB: {e}")
            return []
    
    def count_submissions(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count submissions with optional filters"""
        if not self.is_available():
            return 0
        
        try:
            if filters:
                return self.db.submissions.count_documents(filters)
            else:
                return self.db.submissions.count_documents({})
        except Exception as e:
            print(f"Error counting submissions in MongoDB: {e}")
            return 0
    
    def get_recent_submissions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent submissions"""
        if not self.is_available():
            return []
        
        try:
            cursor = self.db.submissions.find(
                {},
                {"_id": 0, "comments": 0}  # Exclude ObjectId and comments for privacy
            ).sort("created_at", -1).limit(limit)
            
            return list(cursor)
        except Exception as e:
            print(f"Error fetching recent submissions from MongoDB: {e}")
            return []
    
    def save_metric(self, metric_name: str, value: int = 1, metadata: Optional[Dict] = None) -> bool:
        """Save metric to MongoDB"""
        if not self.is_available():
            return False
        
        try:
            metric_data = {
                'metric_name': metric_name,
                'value': value,
                'timestamp': datetime.utcnow(),
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'hour': datetime.utcnow().strftime('%Y-%m-%d:%H'),
                'metadata': metadata or {}
            }
            
            result = self.db.metrics.insert_one(metric_data)
            return result.acknowledged
        except Exception as e:
            print(f"Error saving metric to MongoDB: {e}")
            return False
    
    def get_metrics_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics summary for a specific date or today"""
        if not self.is_available():
            return {}
        
        try:
            target_date = date or datetime.utcnow().strftime('%Y-%m-%d')
            
            pipeline = [
                {"$match": {"date": target_date}},
                {"$group": {
                    "_id": "$metric_name",
                    "total": {"$sum": "$value"},
                    "count": {"$sum": 1}
                }}
            ]
            
            results = list(self.db.metrics.aggregate(pipeline))
            
            # Convert to readable format
            summary = {}
            for result in results:
                summary[result['_id']] = {
                    'total': result['total'],
                    'count': result['count']
                }
            
            return summary
        except Exception as e:
            print(f"Error getting metrics summary from MongoDB: {e}")
            return {}
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.mongo_available = False

# Global MongoDB instance
mongo_helper = MongoHelper()

def migrate_json_to_mongo():
    """Migrate existing JSON submissions to MongoDB"""
    if not mongo_helper.is_available():
        print("MongoDB not available for migration")
        return False
    
    import json
    tracking_file = "submissions_tracking.json"
    
    if not os.path.exists(tracking_file):
        print("No existing submissions to migrate")
        return True
    
    try:
        with open(tracking_file, 'r') as f:
            tracking_data = json.load(f)
        
        migrated_count = 0
        for submission_id, data in tracking_data.items():
            # Check if already exists
            existing = mongo_helper.get_submission(submission_id)
            if existing:
                continue
            
            # Convert old format to new format
            submission_data = {
                'submission_id': submission_id,
                'email': data.get('email', ''),
                'name': data.get('name', ''),
                'first_name': data.get('name', '').split(' ')[0] if data.get('name') else '',
                'last_name': ' '.join(data.get('name', '').split(' ')[1:]) if data.get('name') else '',
                'phone': '',  # Not stored in old format
                'comments': '',  # Not stored in old format
                'created_at': datetime.fromisoformat(data.get('date', datetime.utcnow().isoformat())),
                'updated_at': datetime.utcnow(),
                'status': 'migrated',
                'email_verified': True,
                'source': 'json_migration'
            }
            
            if mongo_helper.save_submission(submission_data):
                migrated_count += 1
        
        print(f"Migrated {migrated_count} submissions from JSON to MongoDB")
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
