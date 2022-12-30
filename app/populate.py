from app.models import User, Resource, File
from app import db, app

# ------- LEGACY --------------
# for tests only

file1 = File(name="File1")
file2 = File(name="File2")
user1 = User(username='matt',password_hash='ab5f2a',is_admin=False)


with app.app_context():

    u = User.query.filter_by(username='matt').first()
    r = Resource.query.filter_by(name='Resource1').first()
    #u.read_resources.append(r)
    print(u.read_resources[0].all_files[0].name)



    #print(r.all_files[0].name)

    # print(r.owner_id)
    # db.session.add(f1)
    #
    #db.session.commit()