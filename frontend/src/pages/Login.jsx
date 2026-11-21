import { useState } from "react";
import { api } from "../api";


export default function Login(){

    const [form,setForm]=useState({
        email:"",
        password:""
    });


    const submit = async(e)=>{

        e.preventDefault();


        try{

            const data = await api(
                "/auth/login",
                {
                    method:"POST",
                    body:form
                }
            );


            localStorage.setItem(
                "token",
                data.access_token
            );


            localStorage.setItem(
                "role",
                data.role
            );


            alert("Login successful");


        }catch(err){

            alert(err.message);

        }

    };


    return (

        <div>

            <h2>
                Login
            </h2>


            <form onSubmit={submit}>


                <input
                    placeholder="Email"
                    onChange={(e)=>
                        setForm({
                            ...form,
                            email:e.target.value
                        })
                    }
                />


                <input
                    type="password"
                    placeholder="Password"
                    onChange={(e)=>
                        setForm({
                            ...form,
                            password:e.target.value
                        })
                    }
                />


                <button>
                    Login
                </button>


            </form>


        </div>

    );

}