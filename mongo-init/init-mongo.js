// MongoDB initialization script
// This script runs when the container is first created

// Use the solemn_declarations database
db = db.getSiblingDB('solemn_declarations');

// Create collections with proper indexes
db.createCollection('submissions');
db.createCollection('metrics');

// Create indexes for submissions collection
db.submissions.createIndex({ "submission_id": 1 }, { unique: true });
db.submissions.createIndex({ "email": 1 });
db.submissions.createIndex({ "created_at": -1 });
db.submissions.createIndex({ "email": 1, "created_at": -1 });

// Create indexes for metrics collection
db.metrics.createIndex({ "metric_name": 1, "timestamp": -1 });
db.metrics.createIndex({ "date": 1 });

// Insert initial configuration document
db.config.insertOne({
    _id: "app_config",
    version: "1.2.0",
    initialized_at: new Date(),
    description: "Level 7 Feeders Contact Form Database"
});

print("MongoDB initialization completed successfully!");
print("Collections created: submissions, metrics, config");
print("Indexes created for optimal performance");
