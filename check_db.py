"""
데이터베이스 초기화 확인 스크립트
"""
from app_new import create_app
from models import db
from sqlalchemy import inspect

def check_database():
    app = create_app()

    with app.app_context():
        # Inspector 생성
        inspector = inspect(db.engine)

        # 모든 테이블 이름 가져오기
        tables = inspector.get_table_names()

        print("=" * 60)
        print("데이터베이스 초기화 상태 확인")
        print("=" * 60)

        # 예상되는 테이블 목록
        expected_tables = [
            'users',
            'chat_sessions',
            'session_metadata',
            'messages',
            'user_preferences'
        ]

        print(f"\n📊 발견된 테이블 수: {len(tables)}")
        print(f"✅ 예상 테이블 수: {len(expected_tables)}\n")

        if len(tables) == 0:
            print("❌ 테이블이 하나도 없습니다!")
            print("   다음 명령으로 초기화하세요:")
            print("   python")
            print("   >>> from app_new import create_app")
            print("   >>> app = create_app()")
            print("   >>> with app.app_context():")
            print("   ...     from models import db")
            print("   ...     db.create_all()")
            return False

        # 테이블별 상세 정보
        print("테이블 상세 정보:\n")

        all_present = True
        for expected in expected_tables:
            if expected in tables:
                print(f"✅ {expected}")

                # 컬럼 정보 가져오기
                columns = inspector.get_columns(expected)
                print(f"   컬럼 수: {len(columns)}")

                # 주요 컬럼 표시
                col_names = [col['name'] for col in columns]
                print(f"   컬럼: {', '.join(col_names[:5])}", end='')
                if len(col_names) > 5:
                    print(f" ... (외 {len(col_names)-5}개)")
                else:
                    print()

                # 인덱스 정보
                indexes = inspector.get_indexes(expected)
                if indexes:
                    print(f"   인덱스: {len(indexes)}개")

                print()
            else:
                print(f"❌ {expected} - 누락!")
                all_present = False

        # 추가 테이블 확인
        extra_tables = set(tables) - set(expected_tables)
        if extra_tables:
            print("\n⚠️  예상하지 못한 추가 테이블:")
            for table in extra_tables:
                print(f"   - {table}")

        print("\n" + "=" * 60)

        if all_present and len(tables) == len(expected_tables):
            print("🎉 데이터베이스가 완벽하게 초기화되었습니다!")
            print("=" * 60)

            # 데이터베이스 파일 정보
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if 'sqlite:///' in db_uri:
                db_file = db_uri.replace('sqlite:///', '')
                print(f"\n📁 데이터베이스 파일: {db_file}")

                import os
                if os.path.exists(db_file):
                    size = os.path.getsize(db_file)
                    print(f"📦 파일 크기: {size:,} bytes")

            return True
        else:
            print("⚠️  일부 테이블이 누락되었습니다.")
            print("=" * 60)
            return False

if __name__ == '__main__':
    check_database()
