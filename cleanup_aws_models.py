#!/usr/bin/env python3
"""
Script to clean up all models in AWS test schema.
"""
import subprocess
import json
import sys

def run_cmd(cmd, timeout=60):
    """Run a command and return result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result
    except subprocess.TimeoutExpired:
        print(f"[WARN] Command timed out: {' '.join(cmd)}")
        return None

def cleanup_model_versions(model_full_name):
    """Delete all versions of a model."""
    print(f"[INFO] Checking versions for {model_full_name}...")
    
    # List model versions
    versions_cmd = [
        "databricks", "--profile", "e2demo-aws",
        "model-versions", "list", model_full_name
    ]
    
    result = run_cmd(versions_cmd)
    if not result or result.returncode != 0:
        print(f"[WARN] Could not list versions for {model_full_name}")
        return
    
    try:
        versions_data = json.loads(result.stdout)
        if not versions_data:
            print(f"[INFO] No versions found for {model_full_name}")
            return
        
        print(f"[INFO] Found {len(versions_data)} versions for {model_full_name}")
        
        # Delete each version
        for version_info in versions_data:
            version = str(version_info.get('version', ''))
            print(f"[INFO] Deleting version {version}...")
            delete_version_cmd = [
                "databricks", "--profile", "e2demo-aws",
                "model-versions", "delete", model_full_name, version
            ]
            
            result = run_cmd(delete_version_cmd, timeout=30)
            if result and result.returncode == 0:
                print(f"[OK] Deleted version {version}")
            else:
                print(f"[WARN] Failed to delete version {version}")
                if result:
                    print(f"[WARN] Error: {result.stderr}")
                    
    except json.JSONDecodeError:
        print(f"[WARN] Could not parse versions JSON for {model_full_name}")
        return

def cleanup_model(model_full_name):
    """Delete a model after cleaning up its versions."""
    print(f"\n[INFO] Cleaning up model: {model_full_name}")
    
    # Clean up versions first
    cleanup_model_versions(model_full_name)
    
    # Delete the model
    print(f"[INFO] Deleting model {model_full_name}...")
    delete_model_cmd = [
        "databricks", "--profile", "e2demo-aws",
        "registered-models", "delete", model_full_name
    ]
    
    result = run_cmd(delete_model_cmd)
    if result and result.returncode == 0:
        print(f"[OK] Deleted model {model_full_name}")
        return True
    else:
        print(f"[WARN] Failed to delete model {model_full_name}")
        if result:
            print(f"[WARN] Error: {result.stderr}")
        return False

def main():
    print("🧹 Starting AWS UC model cleanup...")
    
    # List all models
    list_cmd = [
        "databricks", "--profile", "e2demo-aws", 
        "registered-models", "list",
        "--catalog-name", "jas_test_mlops",
        "--schema-name", "test"
    ]
    
    result = run_cmd(list_cmd)
    if not result or result.returncode != 0:
        print("[ERROR] Failed to list models")
        sys.exit(1)
    
    models_data = json.loads(result.stdout)
    print(f"[INFO] Found {len(models_data)} models to delete")
    
    deleted_count = 0
    failed_count = 0
    
    for model in models_data:
        model_name = model.get('name', '')
        full_name = model.get('full_name', '')
        
        if cleanup_model(full_name):
            deleted_count += 1
        else:
            failed_count += 1
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"✅ Successfully deleted: {deleted_count} models")
    print(f"❌ Failed to delete: {failed_count} models")
    print(f"🎯 Total processed: {len(models_data)} models")
    
    if failed_count == 0:
        print("🎉 All models cleaned up successfully!")
    else:
        print("⚠️  Some models failed to delete - check logs above")

if __name__ == "__main__":
    main()