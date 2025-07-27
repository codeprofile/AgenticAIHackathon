# ============================================================================
# app/services/market_data_sync.py - Data Synchronization Service
# ============================================================================
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import json
import asyncio
from ..database.database import *
from ..database.models import *
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class MarketDataSyncService:
    """Service to sync market data from Government API to local database"""

    def __init__(self):
        self.api_key = '579b464db66ec23bdd00000144dbb7c15318403c464dffb5257ab598'
        self.resource_id = '9ef84268-d588-465a-a308-a864a43d0070'
        self.base_url = f'https://api.data.gov.in/resource/{self.resource_id}'
        self.max_retries = 3
        self.retry_delay = 2

    async def sync_latest_data(self, force_full_sync: bool = False) -> Dict[str, Any]:
        """Sync latest market data"""
        start_time = time.time()

        with get_db_session() as db:
            # Check last sync
            last_sync = db.query(DataSyncLog).filter(
                DataSyncLog.status == 'success'
            ).order_by(desc(DataSyncLog.sync_date)).first()

            sync_type = 'full' if not last_sync or force_full_sync else 'incremental'

            try:
                if sync_type == 'full':
                    result = await self._full_sync(db)
                else:
                    result = await self._incremental_sync(db, last_sync.sync_date)

                # Log successful sync
                duration = time.time() - start_time
                sync_log = DataSyncLog(
                    sync_date=datetime.now(),
                    sync_type=sync_type,
                    status='success',
                    records_processed=result['processed'],
                    records_inserted=result['inserted'],
                    records_updated=result['updated'],
                    duration_seconds=duration
                )
                db.add(sync_log)

                # Generate analytics after sync
                await self._generate_analytics(db)

                logger.info(f"Market data sync completed: {result}")
                return {
                    'status': 'success',
                    'sync_type': sync_type,
                    'duration': duration,
                    **result
                }

            except Exception as e:
                # Log failed sync
                sync_log = DataSyncLog(
                    sync_date=datetime.now(),
                    sync_type=sync_type,
                    status='failed',
                    error_message=str(e),
                    duration_seconds=time.time() - start_time
                )
                db.add(sync_log)
                logger.error(f"Market data sync failed: {e}")
                raise

    async def _full_sync(self, db: Session) -> Dict[str, int]:
        """Perform full data synchronization"""
        logger.info("Starting full market data sync...")

        # Get data from last 7 days to have trend calculation data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        all_records = []
        processed = 0

        # Fetch data day by day for better API reliability
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%d-%m-%Y")

            try:
                records = await self._fetch_api_data(date_filter=date_str)
                all_records.extend(records)
                processed += len(records)
                logger.info(f"Fetched {len(records)} records for {date_str}")

                # Rate limiting
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.warning(f"Failed to fetch data for {date_str}: {e}")

            current_date += timedelta(days=1)

        # Process and store records
        inserted, updated = await self._process_records(db, all_records)

        return {
            'processed': processed,
            'inserted': inserted,
            'updated': updated
        }

    async def _incremental_sync(self, db: Session, last_sync_date: datetime) -> Dict[str, int]:
        """Perform incremental data synchronization"""
        logger.info(f"Starting incremental sync from {last_sync_date}")

        # Get data from last sync date to now
        today = datetime.now().strftime("%d-%m-%Y")

        try:
            records = await self._fetch_api_data(date_filter=today)
            processed = len(records)

            # Process and store records
            inserted, updated = await self._process_records(db, records)

            return {
                'processed': processed,
                'inserted': inserted,
                'updated': updated
            }

        except Exception as e:
            logger.error(f"Incremental sync failed: {e}")
            raise

    async def _fetch_api_data(self, date_filter: str = None, limit: int = 1000) -> List[Dict]:
        """Fetch data from Government API"""
        all_records = []
        offset = 0

        while True:
            params = {
                'api-key': self.api_key,
                'format': 'json',
                'limit': limit,
                'offset': offset
            }

            if date_filter:
                params['filters[arrival_date]'] = date_filter

            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                records = data.get('records', [])

                if not records:
                    break

                all_records.extend(records)
                offset += limit

                # Rate limiting
                time.sleep(1)

            except Exception as e:
                logger.error(f"API request failed: {e}")
                if len(all_records) == 0:
                    raise
                break

        logger.info(f"Fetched {len(all_records)} total records from API")
        return all_records

    async def _process_records(self, db: Session, records: List[Dict]) -> tuple:
        """Process and store records in database"""
        inserted = 0
        updated = 0

        for record in records:
            try:
                # Clean and validate data
                cleaned_record = self._clean_record(record)
                if not cleaned_record:
                    continue

                # Check if record exists
                existing = db.query(MarketPrice).filter(
                    and_(
                        MarketPrice.state == cleaned_record['state'],
                        MarketPrice.district == cleaned_record['district'],
                        MarketPrice.market == cleaned_record['market'],
                        MarketPrice.commodity == cleaned_record['commodity'],
                        MarketPrice.arrival_date == cleaned_record['arrival_date']
                    )
                ).first()

                if existing:
                    # Update existing record
                    for key, value in cleaned_record.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                    updated += 1
                else:
                    # Insert new record
                    market_price = MarketPrice(**cleaned_record)
                    db.add(market_price)
                    inserted += 1

                # Commit in batches
                if (inserted + updated) % 100 == 0:
                    db.commit()

            except Exception as e:
                logger.warning(f"Failed to process record: {e}")
                continue

        # Calculate trends for new/updated records
        await self._calculate_trends(db)

        logger.info(f"Processed records: {inserted} inserted, {updated} updated")
        return inserted, updated

    def _clean_record(self, record: Dict) -> Dict[str, Any]:
        """Clean and validate a single record"""
        try:
            # Parse arrival date
            arrival_date = datetime.strptime(record['arrival_date'], '%d-%m-%Y')

            # Convert prices to float
            min_price = float(record.get('min_price', 0) or 0)
            max_price = float(record.get('max_price', 0) or 0)
            modal_price = float(record.get('modal_price', 0) or 0)

            # Validate essential fields
            if not all([record.get('state'), record.get('district'),
                        record.get('market'), record.get('commodity')]):
                return None

            if modal_price <= 0:
                return None

            return {
                'state': record['state'].strip(),
                'district': record['district'].strip(),
                'market': record['market'].strip(),
                'commodity': record['commodity'].strip(),
                'variety': record.get('variety', '').strip(),
                'grade': record.get('grade', '').strip(),
                'arrival_date': arrival_date,
                'min_price': min_price,
                'max_price': max_price,
                'modal_price': modal_price
            }

        except Exception as e:
            logger.warning(f"Record cleaning failed: {e}")
            return None

    async def _calculate_trends(self, db: Session):
        """Calculate price trends and changes"""
        # Get unique commodities from recent data
        commodities = db.query(MarketPrice.commodity).distinct().all()

        for (commodity,) in commodities:
            try:
                # Get last 7 days of data for this commodity
                recent_data = db.query(MarketPrice).filter(
                    and_(
                        MarketPrice.commodity == commodity,
                        MarketPrice.arrival_date >= datetime.now() - timedelta(days=7)
                    )
                ).order_by(MarketPrice.arrival_date.desc()).all()

                if len(recent_data) < 2:
                    continue

                # Calculate trends
                for i, record in enumerate(recent_data):
                    if i < len(recent_data) - 1:
                        previous_price = recent_data[i + 1].modal_price
                        current_price = record.modal_price

                        price_change = current_price - previous_price
                        percentage_change = (price_change / previous_price) * 100 if previous_price > 0 else 0

                        # Determine trend
                        if percentage_change > 2:
                            trend = 'up'
                        elif percentage_change < -2:
                            trend = 'down'
                        else:
                            trend = 'stable'

                        # Update record
                        record.price_change = round(price_change, 2)
                        record.percentage_change = round(percentage_change, 2)
                        record.trend = trend

            except Exception as e:
                logger.warning(f"Trend calculation failed for {commodity}: {e}")

    async def _generate_analytics(self, db: Session):
        """Generate market analytics"""
        logger.info("Generating market analytics...")

        # Get unique commodities
        commodities = db.query(MarketPrice.commodity).distinct().all()
        analysis_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for (commodity,) in commodities:
            try:
                # Get recent data for this commodity
                recent_data = db.query(MarketPrice).filter(
                    and_(
                        MarketPrice.commodity == commodity,
                        MarketPrice.arrival_date >= datetime.now() - timedelta(days=30)
                    )
                ).all()

                if not recent_data:
                    continue

                # Calculate analytics
                prices = [r.modal_price for r in recent_data]
                avg_price = sum(prices) / len(prices)
                highest_price = max(prices)
                lowest_price = min(prices)

                # Calculate volatility (standard deviation)
                variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
                volatility = variance ** 0.5

                # Find top market
                top_market_data = max(recent_data, key=lambda x: x.modal_price)

                # Calculate trends
                weekly_data = [r for r in recent_data if r.arrival_date >= datetime.now() - timedelta(days=7)]
                monthly_data = recent_data

                weekly_trend = self._calculate_trend_direction(weekly_data)
                monthly_trend = self._calculate_trend_direction(monthly_data)

                # Simple price prediction (linear trend)
                predicted_7d, predicted_14d, confidence = self._predict_prices(recent_data)

                # Create or update analytics record
                existing = db.query(MarketAnalytics).filter(
                    and_(
                        MarketAnalytics.commodity == commodity,
                        MarketAnalytics.analysis_date == analysis_date
                    )
                ).first()

                analytics_data = {
                    'commodity': commodity,
                    'analysis_date': analysis_date,
                    'avg_price': round(avg_price, 2),
                    'highest_price': highest_price,
                    'lowest_price': lowest_price,
                    'price_volatility': round(volatility, 2),
                    'total_markets': len(set((r.state, r.district, r.market) for r in recent_data)),
                    'active_markets': len(recent_data),
                    'top_market': f"{top_market_data.market}, {top_market_data.district}",
                    'top_market_price': top_market_data.modal_price,
                    'weekly_trend': weekly_trend,
                    'monthly_trend': monthly_trend,
                    'predicted_price_7d': predicted_7d,
                    'predicted_price_14d': predicted_14d,
                    'prediction_confidence': confidence,
                    'market_distribution': json.dumps(self._get_market_distribution(recent_data)),
                    'price_history': json.dumps(self._get_price_history(recent_data)),
                    'recommendations': json.dumps(self._generate_recommendations(recent_data, weekly_trend))
                }

                if existing:
                    for key, value in analytics_data.items():
                        setattr(existing, key, value)
                else:
                    analytics = MarketAnalytics(**analytics_data)
                    db.add(analytics)

            except Exception as e:
                logger.warning(f"Analytics generation failed for {commodity}: {e}")

        logger.info("Market analytics generated successfully")

    def _calculate_trend_direction(self, data: List[MarketPrice]) -> str:
        """Calculate trend direction from price data"""
        if len(data) < 2:
            return 'stable'

        # Sort by date
        sorted_data = sorted(data, key=lambda x: x.arrival_date)

        # Calculate average price change
        total_change = 0
        comparisons = 0

        for i in range(1, len(sorted_data)):
            change = sorted_data[i].modal_price - sorted_data[i - 1].modal_price
            total_change += change
            comparisons += 1

        if comparisons == 0:
            return 'stable'

        avg_change = total_change / comparisons

        if avg_change > 10:  # Significant upward trend
            return 'up'
        elif avg_change < -10:  # Significant downward trend
            return 'down'
        else:
            return 'stable'

    def _predict_prices(self, data: List[MarketPrice]) -> tuple:
        """Simple price prediction using linear trend"""
        if len(data) < 3:
            avg_price = sum(r.modal_price for r in data) / len(data)
            return avg_price, avg_price, 50.0

        # Sort by date
        sorted_data = sorted(data, key=lambda x: x.arrival_date)

        # Simple linear regression
        n = len(sorted_data)
        sum_x = sum(range(n))
        sum_y = sum(r.modal_price for r in sorted_data)
        sum_xy = sum(i * r.modal_price for i, r in enumerate(sorted_data))
        sum_x2 = sum(i * i for i in range(n))

        # Calculate slope and intercept
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        # Predict future prices
        predicted_7d = intercept + slope * (n + 7)
        predicted_14d = intercept + slope * (n + 14)

        # Calculate confidence based on data consistency
        recent_volatility = self._calculate_recent_volatility(sorted_data[-7:])
        confidence = max(30, min(90, 80 - recent_volatility))

        return round(predicted_7d, 2), round(predicted_14d, 2), round(confidence, 1)

    def _calculate_recent_volatility(self, data: List[MarketPrice]) -> float:
        """Calculate recent price volatility"""
        if len(data) < 2:
            return 0

        prices = [r.modal_price for r in data]
        avg_price = sum(prices) / len(prices)
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        volatility = (variance ** 0.5 / avg_price) * 100 if avg_price > 0 else 0

        return volatility

    def _get_market_distribution(self, data: List[MarketPrice]) -> Dict:
        """Get market distribution data"""
        market_counts = {}
        for record in data:
            market_key = f"{record.market}, {record.district}"
            market_counts[market_key] = market_counts.get(market_key, 0) + 1

        # Get top 10 markets
        sorted_markets = sorted(market_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'top_markets': dict(sorted_markets),
            'total_markets': len(market_counts),
            'total_entries': len(data)
        }

    def _get_price_history(self, data: List[MarketPrice]) -> List[Dict]:
        """Get price history for charting"""
        # Group by date and calculate average price
        date_prices = {}
        for record in data:
            date_key = record.arrival_date.strftime('%Y-%m-%d')
            if date_key not in date_prices:
                date_prices[date_key] = []
            date_prices[date_key].append(record.modal_price)

        # Calculate average price per date
        history = []
        for date_key in sorted(date_prices.keys()):
            avg_price = sum(date_prices[date_key]) / len(date_prices[date_key])
            history.append({
                'date': date_key,
                'price': round(avg_price, 2),
                'count': len(date_prices[date_key])
            })

        return history[-30:]  # Last 30 days

    def _generate_recommendations(self, data: List[MarketPrice], trend: str) -> List[str]:
        """Generate market recommendations"""
        recommendations = []

        if trend == 'up':
            recommendations.extend([
                "कीमतें बढ़ रही हैं - बेचने का अच्छा समय है",
                "मांग अच्छी है - गुणवत्ता पर ध्यान दें",
                "भंडारण की जरूरत नहीं - तुरंत बेचें"
            ])
        elif trend == 'down':
            recommendations.extend([
                "कीमतें गिर रही हैं - अगर संभव हो तो इंतजार करें",
                "बेहतर मंडी की तलाश करें",
                "गुणवत्ता बनाए रखने पर फोकस करें"
            ])
        else:
            recommendations.extend([
                "कीमतें स्थिर हैं - नियमित बिक्री करें",
                "मार्केट रिसर्च करके बेचें",
                "लागत कम करने पर ध्यान दें"
            ])

        # Add general recommendations
        if len(data) > 0:
            avg_price = sum(r.modal_price for r in data) / len(data)
            top_price = max(r.modal_price for r in data)

            if (top_price - avg_price) / avg_price > 0.2:
                recommendations.append(f"सबसे अच्छी मंडी में 20% ज्यादा दाम मिल रहा है")

        return recommendations
