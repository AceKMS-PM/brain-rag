#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::sync::Mutex;

static BACKEND_PID: Mutex<Option<u32>> = Mutex::new(None);

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}

#[tauri::command]
fn start_backend() -> Result<String, String> {
    let mut pid_guard = BACKEND_PID.lock().map_err(|e| e.to_string())?;
    
    if pid_guard.is_some() {
        return Ok("Backend already running".to_string());
    }
    
    let child = Command::new("/home/kurtdegla/brain/rag-service/venv/bin/python")
        .args(["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
        .current_dir("/home/kurtdegla/brain/rag-service")
        .spawn()
        .map_err(|e| format!("Failed to start backend: {}", e))?;
    
    let pid = child.id();
    *pid_guard = Some(pid);
    
    Ok(format!("Backend started (PID: {})", pid))
}

#[tauri::command]
fn stop_backend() -> Result<String, String> {
    let mut pid_guard = BACKEND_PID.lock().map_err(|e| e.to_string())?;
    
    if let Some(pid) = pid_guard.take() {
        #[cfg(windows)]
        {
            Command::new("taskkill")
                .args(["/F", "/PID", &pid.to_string()])
                .output()
                .map_err(|e| e.to_string())?;
        }
        #[cfg(not(windows))]
        {
            Command::new("kill")
                .arg(pid.to_string())
                .output()
                .map_err(|e| e.to_string())?;
        }
    }
    
    Ok("Backend stopped".to_string())
}

#[tauri::command]
fn get_backend_status() -> String {
    if let Ok(pid_guard) = BACKEND_PID.lock() {
        if pid_guard.is_some() {
            return "running".to_string();
        }
    }
    "stopped".to_string()
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            greet,
            start_backend,
            stop_backend,
            get_backend_status
        ])
        .setup(|_app| {
            // Auto-start backend on window open
            if let Ok(mut pid_guard) = BACKEND_PID.lock() {
                if pid_guard.is_none() {
                    if let Ok(child) = Command::new("python3")
                        .args(["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
                        .current_dir("/home/kurtdegla/brain/rag-service")
                        .spawn()
                    {
                        let pid = child.id();
                        *pid_guard = Some(pid);
                        println!("Backend auto-started with PID {}", pid);
                    }
                }
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
    
    // Cleanup: stop backend when window closes
    let _ = stop_backend();
    println!("App exited, backend stopped");
}