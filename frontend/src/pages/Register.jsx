import { useState } from "react";
import { api } from "../api";


export default function Register() {

    const [form, setForm] = useState({
        name: "",
        email: "",
        password: "",
        role: "author"
    });


    const handleSubmit = async (e) => {
        e.preventDefault();

        try {

            const data = await api(
                "/auth/register",
                {
                    method: "POST",
                    body: form
                }
            );


            alert(data.message);


        } catch (err) {

            alert(err.message);

        }
    };


    return (
        <div>

            <h2>
                Register
            </h2>


            <form onSubmit={handleSubmit}>


                <input
                    placeholder="Name"
                    value={form.name}
                    onChange={(e)=>
                        setForm({
                            ...form,
                            name:e.target.value
                        })
                    }
                />


                <input
                    placeholder="Email"
                    value={form.email}
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
                    value={form.password}
                    onChange={(e)=>
                        setForm({
                            ...form,
                            password:e.target.value
                        })
                    }
                />


                <select
                    value={form.role}
                    onChange={(e)=>
                        setForm({
                            ...form,
                            role:e.target.value
                        })
                    }
                >

                    <option value="author">
                        Author
                    </option>

                    <option value="reviewer">
                        Reviewer
                    </option>

                </select>


                <button type="submit">
                    Register
                </button>


            </form>

        </div>
    );
}