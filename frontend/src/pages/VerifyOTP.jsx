import {useState} from "react";
import {api} from "../api";


export default function VerifyOTP(){

const [data,setData]=useState({
    email:"",
    code:""
});


const submit=async(e)=>{

e.preventDefault();


try{

const res=await api(
"/auth/verify-otp",
{
method:"POST",
body:data
}
);


alert(res.message);


}catch(err){

alert(err.message);

}

};


return (

<div>

<h2>
Verify OTP
</h2>


<form onSubmit={submit}>


<input
placeholder="Email"
onChange={
e=>setData({
...data,
email:e.target.value
})
}
/>


<input
placeholder="OTP Code"
onChange={
e=>setData({
...data,
code:e.target.value
})
}
/>


<button>
Verify
</button>


</form>


</div>

);


}