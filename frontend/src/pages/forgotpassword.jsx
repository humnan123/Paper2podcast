import { useState } from "react";
import { api } from "../api";


export default function ForgotPassword(){

    const [email,setEmail] = useState("");


    const submit = async(e)=>{

        e.preventDefault();


        try{

            const data = await api(
                "/auth/forgot-password",
                {
                    method:"POST",
                    body:{
                        email
                    }
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
                Forgot Password
            </h2>


            <form onSubmit={submit}>


                <input
                    placeholder="Email"
                    value={email}
                    onChange={
                        e=>setEmail(e.target.value)
                    }
                />


                <button>
                    Send Reset OTP
                </button>


            </form>


        </div>

    );

}