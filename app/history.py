from flask import render_template, session
from app import webapp

import mysql.connector



@webapp.route('/history',methods=['GET'])
# Display an HTML list of all courses.
def history():
    # auth check
    if 'role' in session and 'username' in session and 'user_id' in session:
        user_id = session["user_id"]
        cnx = mysql.connector.connect(user='root', 
                                    password='ece1779pass',
                                    host='127.0.0.1',
                                    database='1779projcet1')

        cursor = cnx.cursor()
        query = "SELECT * FROM tbl_image WHERE user_id = %s"
        cursor.execute(query, (user_id,))



        #print(txt[txt.rfind('/')+1:])

        beforeAI = [[],[],[],[]]
        afterAI = [[],[],[],[]]
        for i in cursor:
            if i[3] == 1:
                tmp=i[2]
                tmp=tmp[tmp.rfind('/')+1:]
                beforeAI[0].append(tmp)
                afterAI[0].append('test_'+tmp)
            elif i[3] == 2:
                tmp=i[2]
                tmp=tmp[tmp.rfind('/')+1:]
                beforeAI[1].append(tmp)
                afterAI[1].append('test_'+tmp)
            elif i[3] == 3:
                tmp=i[2]
                tmp=tmp[tmp.rfind('/')+1:]
                beforeAI[2].append(tmp)
                afterAI[2].append('test_'+tmp)
            elif i[3] == 4:
                tmp=i[2]
                tmp=tmp[tmp.rfind('/')+1:]
                beforeAI[3].append(tmp)
                afterAI[3].append('test_'+tmp)
            print(i)
        print(beforeAI)
        print(afterAI)

        view = render_template("history/history.html",title="Upload history", beforeAI=beforeAI, afterAI=afterAI)


        cnx.close()
        return view
    else:
        return render_template("/login/login.html", error_msg = "Please sign in first")
