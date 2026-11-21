import { useState } from "react";
import { api } from "../api";


export default function ResetPassword(){

    const [form,setForm] = useState({
        email:"",
        code:"",
        new_password:""
    });



    const submit = async(e)=>{

        e.preventDefault();


        try{

            const data = await api(
                "/auth/reset-password",
                {
                    method:"POST",
                    body:form
                }
            );


            alert(data.message);


        }catch(err){

            alert(err.message);

        }

    };



    return (

        <div>

            <h2>
                Reset Password
            </h2>


            <form onSubmit={submit}>


                <input
                    placeholder="Email"
                    onChange={
                        e=>setForm({
                            ...form,
                            email:e.target.value
                        })
                    }
                />


                <input
                    placeholder="Reset OTP"
                    onChange={
                        e=>setForm({
                            ...form,
                            code:e.target.value
                        })
                    }
                />


                <input
                    type="password"
                    placeholder="New Password"
                    onChange={
                        e=>setForm({
                            ...form,
                            new_password:e.target.value
                        })
                    }
                />


                <button>
                    Reset Password
                </button>


            </form>


        </div>

    );

}