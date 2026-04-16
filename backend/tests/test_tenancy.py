
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import tenant_context
from uuid import uuid4

def test_tenant_isolation():
    print("Running Tenancy Context Test...")
    
    # Scenario 1: No tenant set
    assert tenant_context.get() is None
    print("✅ Scenario 1: Default context is None")
    
    # Scenario 2: Set tenant A
    tenant_a = uuid4()
    token = tenant_context.set(tenant_a)
    assert tenant_context.get() == tenant_a
    print(f"✅ Scenario 2: Context set to Tenant A ({tenant_a})")
    
    # Scenario 3: Reset context
    tenant_context.reset(token)
    assert tenant_context.get() is None
    print("✅ Scenario 3: Context reset successfully")
    
    # Scenario 4: Simulate a request flow
    tenant_b = uuid4()
    tenant_context.set(tenant_b)
    assert tenant_context.get() == tenant_b
    print(f"✅ Scenario 4: Context set to Tenant B ({tenant_b})")

if __name__ == '__main__':
    try:
        test_tenant_isolation()
        print('\nOverall Result: SUCCESS')
    except Exception as e:
        print(f'\nOverall Result: FAILED - {e}')
        sys.exit(1)
