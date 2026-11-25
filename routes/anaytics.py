
from database.db import get_db


def get_analytics_data():

    conn = get_db()

    try:
        cursor = conn.cursor()

        # Daily food statistics
        cursor.execute("""
            SELECT
                meal_date,
                COALESCE(SUM(prepared), 0) AS prepared,
                COALESCE(SUM(consumed), 0) AS consumed,
                COALESCE(SUM(wasted), 0) AS wasted
            FROM meals
            GROUP BY meal_date
            ORDER BY meal_date ASC
        """)

        records = cursor.fetchall()

        dates = []
        prepared = []
        consumed = []
        wasted = []

        for row in records:
            dates.append(row["meal_date"])
            prepared.append(row["prepared"])
            consumed.append(row["consumed"])
            wasted.append(row["wasted"])

        # Overall totals
        total_prepared = sum(prepared)
        total_consumed = sum(consumed)
        total_wasted = sum(wasted)

        # Food waste percentage
        waste_percentage = (
            round((total_wasted / total_prepared) * 100, 2)
            if total_prepared > 0 else 0
        )

        # Food utilization percentage
        utilization_percentage = (
            round((total_consumed / total_prepared) * 100, 2)
            if total_prepared > 0 else 0
        )

        return {
            "dates": dates,
            "prepared": prepared,
            "consumed": consumed,
            "wasted": wasted,
            "total_prepared": total_prepared,
            "total_consumed": total_consumed,
            "total_wasted": total_wasted,
            "waste_percentage": waste_percentage,
            "utilization_percentage": utilization_percentage
        }

    finally:
        conn.close()
