from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func, desc
from datetime import datetime, timedelta

from app.database import get_db
from app.models.customer import Customer, AccountType, CustomerStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.utils.security import get_current_user, TokenData

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/", response_model=dict)
async def get_customers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in name, account_no"),
    account_type: Optional[AccountType] = Query(None, description="Filter by account type"),
    status: Optional[CustomerStatus] = Query(None, description="Filter by status"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get list of customers with advanced filtering, pagination and sorting
    """
    try:
        # Build base query
        query = select(Customer).where(Customer.is_deleted == False)
        count_query = select(func.count()).select_from(Customer).where(Customer.is_deleted == False)
        
        # Apply filters
        filters = []
        
        if search:
            search_filter = f"%{search.strip()}%"
            filters.append(
                Customer.name.ilike(search_filter) |
                Customer.account_no.ilike(search_filter) |
                Customer.email.ilike(search_filter)
            )
        
        if account_type:
            filters.append(Customer.account_type == account_type)
            
        if status:
            filters.append(Customer.status == status)
            
        if branch:
            filters.append(Customer.branch.ilike(f"%{branch}%"))
        
        if filters:
            filter_condition = and_(*filters)
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply sorting
        sort_column = getattr(Customer, sort_by, Customer.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        customers = result.scalars().all()
        
        return {
            "items": [CustomerResponse.from_orm(customer) for customer in customers],
            "total": total,
            "page": (skip // limit) + 1,
            "page_size": limit,
            "pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve customers: {str(e)}"
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get customer details by ID
    """
    try:
        query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.is_deleted == False
            )
        )
        result = await db.execute(query)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        return CustomerResponse.from_orm(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve customer: {str(e)}"
        )


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new customer
    """
    try:
        # Check if account_no already exists
        existing_query = select(Customer).where(
            and_(
                Customer.account_no == customer_data.account_no,
                Customer.is_deleted == False
            )
        )
        existing_result = await db.execute(existing_query)
        existing_customer = existing_result.scalar_one_or_none()
        
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this account number already exists"
            )
        
        # Create new customer
        db_customer = Customer(
            **customer_data.model_dump(),
            created_at=datetime.utcnow()
        )
        
        db.add(db_customer)
        await db.commit()
        await db.refresh(db_customer)
        
        return CustomerResponse.from_orm(db_customer)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create customer: {str(e)}"
        )


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update customer information
    """
    try:
        # Check if customer exists
        query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.is_deleted == False
            )
        )
        result = await db.execute(query)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Check if account_no is being changed and if it already exists
        update_data = customer_data.model_dump(exclude_unset=True)
        if "account_no" in update_data and update_data["account_no"] != customer.account_no:
            existing_query = select(Customer).where(
                and_(
                    Customer.account_no == update_data["account_no"],
                    Customer.id != customer_id,
                    Customer.is_deleted == False
                )
            )
            existing_result = await db.execute(existing_query)
            existing_customer = existing_result.scalar_one_or_none()
            
            if existing_customer:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Another customer with this account number already exists"
                )
        
        # Update customer fields
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        customer.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(customer)
        
        return CustomerResponse.from_orm(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update customer: {str(e)}"
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    permanent: bool = Query(False, description="Permanently delete (admin only)"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Delete a customer (soft delete by default, permanent if specified)
    """
    try:
        # Check if customer exists
        query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.is_deleted == False
            )
        )
        result = await db.execute(query)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Check for related facilities
        from app.models.facility import Facility
        facilities_query = select(func.count()).select_from(Facility).where(
            and_(
                Facility.customer_id == customer_id,
                Facility.is_deleted == False
            )
        )
        facilities_result = await db.execute(facilities_query)
        facilities_count = facilities_result.scalar() or 0
        
        if facilities_count > 0 and permanent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot permanently delete customer with {facilities_count} active facilities"
            )
        
        if permanent:
            # Permanent delete (admin only - would need role check)
            await db.delete(customer)
        else:
            # Soft delete
            customer.is_deleted = True
            customer.status = CustomerStatus.INACTIVE
            customer.updated_at = datetime.utcnow()
        
        await db.commit()
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete customer: {str(e)}"
        )


@router.post("/{customer_id}/restore", response_model=CustomerResponse)
async def restore_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Restore a soft-deleted customer
    """
    try:
        # Find soft-deleted customer
        query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.is_deleted == True
            )
        )
        result = await db.execute(query)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deleted customer not found"
            )
        
        # Check if account_no conflicts with existing active customer
        conflict_query = select(Customer).where(
            and_(
                Customer.account_no == customer.account_no,
                Customer.id != customer_id,
                Customer.is_deleted == False
            )
        )
        conflict_result = await db.execute(conflict_query)
        conflict_customer = conflict_result.scalar_one_or_none()
        
        if conflict_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot restore: Account number conflicts with existing customer"
            )
        
        # Restore customer
        customer.is_deleted = False
        customer.status = CustomerStatus.ACTIVE
        customer.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(customer)
        
        return CustomerResponse.from_orm(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore customer: {str(e)}"
        )


@router.get("/{customer_id}/facilities")
async def get_customer_facilities(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get all facilities for a specific customer
    """
    try:
        # Check if customer exists
        customer_query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.is_deleted == False
            )
        )
        customer_result = await db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Get customer facilities
        from app.models.facility import Facility
        facilities_query = select(Facility).where(
            and_(
                Facility.customer_id == customer_id,
                Facility.is_deleted == False
            )
        ).order_by(desc(Facility.created_at))
        
        facilities_result = await db.execute(facilities_query)
        facilities = facilities_result.scalars().all()
        
        return {
            "customer": CustomerResponse.from_orm(customer),
            "facilities": facilities,
            "total_facilities": len(facilities),
            "total_amount": sum(float(f.amount) for f in facilities if f.amount),
            "total_outstanding": sum(float(f.outstanding) for f in facilities if f.outstanding)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve customer facilities: {str(e)}"
        )


@router.get("/stats/summary")
async def get_customers_summary(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get customer statistics summary
    """
    try:
        # Total customers
        total_query = select(func.count()).select_from(Customer).where(Customer.is_deleted == False)
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0
        
        # Active customers
        active_query = select(func.count()).select_from(Customer).where(
            and_(Customer.is_deleted == False, Customer.status == CustomerStatus.ACTIVE)
        )
        active_result = await db.execute(active_query)
        active = active_result.scalar() or 0
        
        # By account type
        type_query = select(Customer.account_type, func.count()).where(
            Customer.is_deleted == False
        ).group_by(Customer.account_type)
        type_result = await db.execute(type_query)
        by_type = {row[0].value: row[1] for row in type_result.fetchall()}
        
        # By status
        status_query = select(Customer.status, func.count()).where(
            Customer.is_deleted == False
        ).group_by(Customer.status)
        status_result = await db.execute(status_query)
        by_status = {row[0].value: row[1] for row in status_result.fetchall()}
        
        # Recent customers (last 30 days)
        recent_date = datetime.utcnow() - timedelta(days=30)
        recent_query = select(func.count()).select_from(Customer).where(
            and_(Customer.is_deleted == False, Customer.created_at >= recent_date)
        )
        recent_result = await db.execute(recent_query)
        recent = recent_result.scalar() or 0

        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_type": by_type,
            "by_status": by_status,
            "recent_30_days": recent
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve customer summary: {str(e)}"
        )