import os
import time
import socket
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Database Configuration from Environment Variables
DB_HOST = os.getenv("DB_HOST", "taskmanager-db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "taskdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgrespassword")
APP_PORT = int(os.getenv("APP_PORT", "5000"))

def get_db_connection(max_retries=5, delay=2):
    """Establishes connection to the PostgreSQL database with retry mechanism."""
    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=5
            )
            return conn
        except Exception as e:
            print(f"[Attempt {attempt}/{max_retries}] Database connection failed: {e}")
            if attempt < max_retries:
                time.sleep(delay)
            else:
                raise e

def init_db():
    """Initializes tables if they do not exist."""
    try:
        conn = get_db_connection(max_retries=8, delay=2)
        with conn.cursor() as cur:
            # Create tasks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    priority VARCHAR(20) DEFAULT 'Medium',
                    category VARCHAR(50) DEFAULT 'General',
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Create visits/analytics table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS page_views (
                    id SERIAL PRIMARY KEY,
                    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT,
                    client_ip VARCHAR(100)
                );
            """)
            # Seed default tasks if empty
            cur.execute("SELECT COUNT(*) FROM tasks;")
            count = cur.fetchone()[0]
            if count == 0:
                cur.execute("""
                    INSERT INTO tasks (title, description, priority, category, completed) VALUES
                    ('Configure Multi-Container Network', 'Ensure web app and database communicate over custom bridge network.', 'High', 'Docker', TRUE),
                    ('Verify Persistent Volume Storage', 'Ensure database state persists when containers are stopped or recreated.', 'High', 'Database', TRUE),
                    ('Automate Lifecycle with Shell Scripts', 'Implement prepare, start, stop, and remove automation scripts.', 'Medium', 'DevOps', TRUE),
                    ('Test Failover & Restart Policy', 'Confirm container restarts automatically on failure using --restart flag.', 'Low', 'Testing', FALSE);
                """)
        conn.commit()
        conn.close()
        print("Database schema successfully initialized.")
    except Exception as e:
        print(f"Warning: DB initialization error: {e}")

# Initialize database schema on startup
try:
    init_db()
except Exception as err:
    print(f"Initial DB check failed (will retry on request): {err}")

@app.route("/")
def index():
    hostname = socket.gethostname()
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Record visit
    total_views = 0
    db_connected = False
    try:
        conn = get_db_connection(max_retries=2, delay=1)
        with conn.cursor() as cur:
            cur.execute("INSERT INTO page_views (user_agent, client_ip) VALUES (%s, %s);", (user_agent, client_ip))
            conn.commit()
            cur.execute("SELECT COUNT(*) FROM page_views;")
            total_views = cur.fetchone()[0]
        conn.close()
        db_connected = True
    except Exception as e:
        print(f"Failed to record view: {e}")
        total_views = "N/A"

    return render_template(
        "index.html",
        hostname=hostname,
        db_host=DB_HOST,
        db_name=DB_NAME,
        db_connected=db_connected,
        total_views=total_views
    )

@app.route("/api/health", methods=["GET"])
def health():
    db_status = "unreachable"
    try:
        conn = get_db_connection(max_retries=1)
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        conn.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "online",
        "service": "taskmanager-web",
        "database": db_status,
        "container_hostname": socket.gethostname(),
        "db_host": DB_HOST,
        "timestamp": time.time()
    }), 200 if db_status == "healthy" else 503

@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    status_filter = request.args.get("status")  # 'completed', 'pending', or None
    search_query = request.args.get("q", "").strip()

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []

            if status_filter == "completed":
                query += " AND completed = TRUE"
            elif status_filter == "pending":
                query += " AND completed = FALSE"

            if search_query:
                query += " AND (title ILIKE %s OR description ILIKE %s OR category ILIKE %s)"
                params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])

            query += " ORDER BY completed ASC, id DESC"
            cur.execute(query, params)
            tasks = cur.fetchall()
        conn.close()
        return jsonify({"success": True, "tasks": tasks})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    priority = data.get("priority", "Medium")
    category = data.get("category", "General")

    if not title:
        return jsonify({"success": False, "error": "Task title is required"}), 400

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO tasks (title, description, priority, category, completed)
                VALUES (%s, %s, %s, %s, FALSE)
                RETURNING *;
                """,
                (title, description, priority, category)
            )
            new_task = cur.fetchone()
            conn.commit()
        conn.close()
        return jsonify({"success": True, "task": new_task}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/tasks/<int:task_id>/toggle", methods=["PUT"])
def toggle_task(task_id):
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE tasks
                SET completed = NOT completed
                WHERE id = %s
                RETURNING *;
                """,
                (task_id,)
            )
            updated_task = cur.fetchone()
            conn.commit()
        conn.close()

        if not updated_task:
            return jsonify({"success": False, "error": "Task not found"}), 404

        return jsonify({"success": True, "task": updated_task})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))
            deleted_id = cur.fetchone()
            conn.commit()
        conn.close()

        if not deleted_id:
            return jsonify({"success": False, "error": "Task not found"}), 404

        return jsonify({"success": True, "message": f"Task {task_id} deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/stats", methods=["GET"])
def get_stats():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM tasks;")
            total_tasks = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM tasks WHERE completed = TRUE;")
            completed_tasks = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM tasks WHERE completed = FALSE;")
            pending_tasks = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM page_views;")
            total_views = cur.fetchone()[0]
        conn.close()
        return jsonify({
            "success": True,
            "stats": {
                "total": total_tasks,
                "completed": completed_tasks,
                "pending": pending_tasks,
                "views": total_views,
                "db_status": "Connected"
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
